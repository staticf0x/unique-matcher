use ini::Ini;
use std::path::{Path, PathBuf};

pub fn get_poe_monitor(workdir: &Path) -> usize {
    let cfg_path = workdir.join("config.ini");
    if !cfg_path.exists() {
        std::fs::write(&cfg_path, "[screenshot]\nscreen = -1\nshortcut = Win+S").unwrap();
    }

    // Load config
    let mut screen_id: i32 = match Ini::load_from_file(&cfg_path) {
        Ok(ini_file) => ini_file
            .get_from_or(Some("screenshot"), "screen", "0")
            .parse()
            .unwrap(),
        Err(_) => 0,
    };

    if screen_id == -1 {
        // Auto-detect
        let poe_config_path = poe_config_path().unwrap();
        screen_id = match active_monitor_number_from_poe_config(poe_config_path) {
            Some(val) => val as i32,
            None => {
                println!("Couldn't auto-detect PoE screen, defaulting to 0");
                0
            }
        }
    }

    screen_id as usize
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
fn active_monitor_number_from_poe_config<P>(poe_config_path: P) -> Option<usize>
where
    P: AsRef<Path>,
{
    let poe_config_path = poe_config_path.as_ref();

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
