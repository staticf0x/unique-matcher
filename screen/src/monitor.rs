use ini::Ini;
use screenshots::Screen;
use std::{
    fmt::Display,
    path::{Path, PathBuf},
};

#[derive(Debug)]
pub enum Error {
    InvalidScreenId { id: usize, total: usize },
}

impl Display for Error {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Error::InvalidScreenId { id, total } => write!(
                f,
                "Error: Cannot use screen {}, you only have {} screen(s) (IDs go from 0 to {})",
                id,
                total,
                total - 1
            ),
        }
    }
}

pub fn poe_screen(workdir: &Path) -> Result<Screen, Error> {
    let id = get_poe_monitor_id(&workdir);

    // Get all screens
    let screens = Screen::all().unwrap();

    let total = screens.len();
    match id >= total {
        true => Err(Error::InvalidScreenId { id, total }),
        false => Ok(screens[id]),
    }
}

pub fn get_poe_monitor_id(workdir: &Path) -> usize {
    if cfg!(windows) {
        match winapi::poe_monitor() {
            Some(n) => n,
            None => get_poe_monitor_id_common(workdir),
        }
    } else {
        get_poe_monitor_id_common(workdir)
    }
}

fn get_poe_monitor_id_common(workdir: &Path) -> usize {
    match from_local_config(workdir) {
        Some(n) => n,
        None => match from_poe_config() {
            Some(n) => n,
            None => 0,
        },
    }
}

/// Read value from local config.ini
/// ```ini
/// [screenshot]
/// screen = 1
/// ````
fn from_local_config(workdir: &Path) -> Option<usize> {
    let cfg_path = workdir.join("config.ini");
    if !cfg_path.exists() {
        std::fs::write(&cfg_path, "[screenshot]\nscreen = -1\nshortcut = Win+S").unwrap();
    }

    // Load config
    let screen_id: i32 = match Ini::load_from_file(&cfg_path) {
        Ok(ini_file) => ini_file
            .get_from_or(Some("screenshot"), "screen", "0")
            .parse()
            .unwrap(),
        Err(_) => 0,
    };

    match screen_id {
        -1 => None,
        _ => Some(screen_id as usize),
    }
}

/// cross-platform C:\Users\username\Documents\My Games\Path of Exile\production_Config.ini
fn poe_config_path() -> Option<PathBuf> {
    dirs_next::document_dir().map(|docs_dir| {
        docs_dir
            .join("My Games")
            .join("Path of Exile")
            .join("production_Config.ini")
    })
}

/// Read poe production_Config.ini, try to find the index of the preferred minitor.
/// Something like this:
///
///  adapter_name=AMD Radeon RX 5700 XT(#0)
///
fn from_poe_config() -> Option<usize> {
    let poe_config_path = poe_config_path().unwrap();

    if !poe_config_path.exists() {
        println!("PoE config path doesn't exist (are you on Linux?)");
        return None;
    }

    let ini_file = Ini::load_from_file(poe_config_path.to_str().unwrap()).unwrap();

    let adapter_name = ini_file.get_from_or(Some("DISPLAY"), "adapter_name", "(#0)");

    let Some(start) = adapter_name.rfind("(#") else {
        return None;
    };

    let Some(end) = adapter_name.rfind(")") else {
        return None;
    };

    let Some(substr) = adapter_name.get(start + 2..end) else {
        return None;
    };

    let monitor_index = substr.parse::<usize>().ok()?;

    Some(monitor_index)
}

mod winapi {
    use std::{cell::RefCell, rc::Rc};

    use windows::{
        Win32::Foundation::*,
        Win32::Graphics::Gdi::{GetMonitorInfoW, MONITORINFO, MONITORINFOEXW, MONITOR_FROM_FLAGS},
        Win32::UI::WindowsAndMessaging::*,
    };

    static mut CLOSURE: Option<Box<dyn Fn(HWND, LPARAM) -> BOOL>> = None;

    pub fn poe_monitor() -> Option<usize> {
        let vec: Rc<RefCell<Vec<usize>>> = Rc::new(RefCell::new(Vec::new()));

        unsafe {
            let vec = vec.clone();
            let closure: Box<dyn Fn(HWND, LPARAM) -> BOOL> =
                Box::new(move |window: HWND, _: LPARAM| -> BOOL {
                    let mut text: [u16; 512] = [0; 512];
                    let len = GetWindowTextW(window, &mut text);
                    let text = String::from_utf16_lossy(&text[..len as usize]);

                    let mut info = WINDOWINFO::default();
                    GetWindowInfo(window, &mut info).unwrap();

                    if text == "Path of Exile"
                        && info.dwStyle.contains(WS_VISIBLE)
                        && !info.dwStyle.contains(WS_MINIMIZE)
                    {
                        let mut rect = RECT::default();
                        GetWindowRect(window, &mut rect).unwrap();

                        let monitor = windows::Win32::Graphics::Gdi::MonitorFromRect(
                            &mut rect,
                            MONITOR_FROM_FLAGS::default(),
                        );

                        let mut monitor_info = MONITORINFOEXW {
                            monitorInfo: MONITORINFO {
                                cbSize: std::mem::size_of::<MONITORINFOEXW>() as u32,
                                ..Default::default()
                            },
                            szDevice: Default::default(),
                        };

                        GetMonitorInfoW(monitor, &mut monitor_info as *mut _ as *mut MONITORINFO);
                        let display_info_string =
                            String::from_utf16_lossy(monitor_info.szDevice.as_ref());

                        display_info_string
                            .find("DISPLAY")
                            .map(|index| display_info_string.get(index + 7..))
                            .map(|c| {
                                c.map(|c| {
                                    c.chars().next().map(|c| {
                                        c.to_digit(10)
                                            .map(|d| vec.borrow_mut().push((d - 1) as usize))
                                    })
                                })
                            });
                    }

                    TRUE
                });

            // Set the global mutable variable to hold the closure
            CLOSURE = Some(closure);

            // Pass the wrapper function's reference to EnumWindows
            EnumWindows(Some(extern_system_wrapper), LPARAM(0)).unwrap();
        }

        let vec = vec.borrow();

        match vec.len() {
            0 => None,
            _ => vec.get(0).copied(),
        }
    }

    extern "system" fn extern_system_wrapper(window: HWND, _: LPARAM) -> BOOL {
        unsafe {
            // Get the closure from the global mutable variable
            if let Some(closure) = &mut CLOSURE {
                // Call the closure
                closure(window, LPARAM(0))
            } else {
                // Return default BOOL if closure is not set
                FALSE
            }
        }
    }
}
