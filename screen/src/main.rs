use chrono::Local;
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

    let screen = monitor::poe_screen(&workdir).unwrap();

    // Prepare image path
    let filename = format!("{}.png", Local::now().format("%Y-%m-%d-%H-%M-%S-%3f"));
    let image_path = screenshots_dir.join(filename);

    // Make screenshot
    let image = screen.capture().unwrap();
    image.save(&image_path).unwrap();

    println!("Screenshot saved to: {}", image_path.display());
}
