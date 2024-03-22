use chrono::Local;
use std::{env, println};

pub mod monitor;

fn main() {
    // Prepare paths
    let workdir = env::current_dir().unwrap();

    let screenshots_dir = workdir.join("data").join("queue");
    if !screenshots_dir.exists() {
        std::fs::create_dir_all(&screenshots_dir).unwrap();
    }

    let screen = monitor::poe_screen(&workdir).unwrap();
    let window = monitor::get_poe_window();

    // Prepare image path
    let filename = format!("{}.png", Local::now().format("%Y-%m-%d-%H-%M-%S-%3f"));
    let image_path = screenshots_dir.join(filename);

    // Make screenshot
    let image = match window {
        Some(win) => {
            let width: u32 = (win.right - win.left).try_into().unwrap();
            let height: u32 = (win.bottom - win.top).try_into().unwrap();
            let is_windowed = (screen.display_info.width > 1920
                && screen.display_info.height > 1080)
                && (width < screen.display_info.width && height < screen.display_info.height);

            if is_windowed {
                // If playing on a larger than 1080p screen, capture only
                // the windowed part of the PoE window. Assuming the player
                // set PoE to 1920x1080, Unique Matcher will work.
                screen
                    .capture_area(win.left, win.top, width, height)
                    .unwrap()
            } else {
                // On 1080p screens just capture the whole screen
                screen.capture().unwrap()
            }
        }
        None => screen.capture().unwrap(),
    };

    image.save(&image_path).unwrap();

    println!("Screenshot saved to: {}", image_path.display());
}
