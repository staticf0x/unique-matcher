use chrono::Local;
use screenshots::Screen;
use std::env;

fn main() {
    // Prepare paths
    let cur_dir = env::current_dir().unwrap();
    let workdir = cur_dir.as_path();
    let screen_dir = workdir.join("data").join("queue");

    // Prepare image path
    let local_time = Local::now();
    let filename = String::from(local_time.format("%Y-%m-%d-%H-%M-%S").to_string())
        + String::from(".png").as_str();
    let image_path_buf = screen_dir.join(filename);
    let image_path = image_path_buf.as_path();

    // Get all screens
    let screens = Screen::all().unwrap();

    // Use the first one
    // TODO: This may be an issue
    let screen = screens[0];

    // Make screenshot
    let image = screen.capture().unwrap();
    image.save(image_path).unwrap();
}
