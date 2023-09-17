use chrono::Local;
use ini::Ini;
use screenshots::Screen;
use std::{env, println};

fn main() {
    // Prepare paths
    let cur_dir = env::current_dir().unwrap();
    let workdir = cur_dir.as_path();
    let screen_dir = workdir.join("data").join("queue");
    let cfg_path = workdir.join("config.ini");
    let config_path_str = cfg_path.as_path().to_str().unwrap();

    // Load config
    let screen_id: usize = match Ini::load_from_file(config_path_str) {
        Ok(ini_file) => ini_file
            .get_from_or(Some("screenshot"), "screen", "0")
            .parse::<usize>()
            .unwrap(),
        Err(_) => 0 as usize,
    };

    println!("Using screen ID: {}", screen_id);

    // Prepare image path
    let local_time = Local::now();
    let filename = String::from(local_time.format("%Y-%m-%d-%H-%M-%S").to_string())
        + String::from(".png").as_str();
    let image_path_buf = screen_dir.join(filename);
    let image_path = image_path_buf.as_path();

    // Get all screens
    let screens = Screen::all().unwrap();

    // Use the first one
    if screen_id >= screens.len() {
        println!(
            "Error: Cannot use screen {}, you only have {} screen(s) (IDs go from 0 to {})",
            screen_id,
            screens.len(),
            screens.len() - 1,
        );
    } else {
        let screen = screens[screen_id];

        // Make screenshot
        let image = screen.capture().unwrap();
        image.save(image_path).unwrap();

        println!("Screenshot saved to: {}", &image_path.to_str().unwrap());
    }
}
