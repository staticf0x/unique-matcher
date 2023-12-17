use chrono::Local;
use screenshots::Screen;
use std::{env, println};

pub mod monitor;

fn main() {
    // Prepare paths
    let cur_dir = env::current_dir().unwrap();
    let workdir = cur_dir.as_path();

    let screenshots_dir = workdir.join("data").join("queue");
    if !screenshots_dir.exists() {
        std::fs::create_dir_all(&screenshots_dir).unwrap();
    }

    let screen_id = monitor::get_poe_monitor(&workdir);

    println!("Using screen ID: {}", screen_id);

    // Prepare image path
    let filename = format!("{}.png", Local::now().format("%Y-%m-%d-%H-%M-%S-%3f"));
    let image_path = screenshots_dir.join(filename);

    // Get all screens
    let screens = Screen::all().unwrap();

    // Use the first one
    if screen_id as usize >= screens.len() {
        println!(
            "Error: Cannot use screen {}, you only have {} screen(s) (IDs go from 0 to {})",
            screen_id,
            screens.len(),
            screens.len() - 1,
        );
    } else {
        let screen = screens[screen_id as usize];

        // Make screenshot
        let image = screen.capture().unwrap();
        image.save(&image_path).unwrap();

        println!("Screenshot saved to: {}", image_path.display());
    }
}
