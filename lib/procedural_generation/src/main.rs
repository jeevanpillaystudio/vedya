use clap::{Arg, ArgAction, Command};
use image::{ImageBuffer, Luma};
use noise::{NoiseFn, Perlin};

fn main() {
    // Define CLI arguments
    let cmd = clap::Command::new("pacman").subcommand(
        Command::new("field").about("Generate a flow field").arg(
            Arg::new("width")
                .short('w')
                .long("width")
                .help("width of the field")
                .action(ArgAction::Set)
                .num_args(1..),
        ), // .arg(
           //     Arg::new("height")
           //         .short('h')
           //         .long("height")
           //         .help("height of the field")
           //         .action(ArgAction::Set)
           //         .num_args(1..),
           // )
           // .arg(
           //     Arg::new("scale")
           //         .short('s')
           //         .long("scale")
           //         .help("scale of the field")
           //         .action(ArgAction::Set)
           //         .num_args(1..),
           // )
           // .arg(
           //     Arg::new("octaves")
           //         .short('o')
           //         .long("octaves")
           //         .help("octaves of the field")
           //         .action(ArgAction::Set)
           //         .num_args(1..),
           // )
           // .arg(
           //     Arg::new("persistence")
           //         .short('p')
           //         .long("persistence")
           //         .help("persistence of the field")
           //         .action(ArgAction::Set)
           //         .num_args(1..),
           // )
           // .arg(
           //     Arg::new("lacunarity")
           //         .short('l')
           //         .long("lacunarity")
           //         .help("lacunarity of the field")
           //         .action(ArgAction::Set)
           //         .num_args(1..),
           // )
           // .arg(
           //     Arg::new("output")
           //         .short('o')
           //         .long("output")
           //         .help("output file")
           //         .action(ArgAction::Set)
           //         .num_args(1..),
           // ),
    );

    let matches = cmd.get_matches();
    match matches.subcommand() {
        Some(("field", matches)) => matches,
        _ => unreachable!("clap should ensure we don't get here"),
    };

    let width = 100;
    let height = 100;
    let scale = 0.1;
    let output = "heightmap.png";

    // Generate the heightmap
    let perlin = Perlin::new(0); // Provide a seed value, e.g., 0
    let mut img = ImageBuffer::new(width, height);

    for y in 0..height {
        for x in 0..width {
            let nx = x as f64 * scale;
            let ny = y as f64 * scale;
            let value = perlin.get([nx, ny]);

            // Normalize the value to be between 0 and 255
            let pixel_value = ((value + 1.0) / 2.0 * 255.0) as u8;
            img.put_pixel(x, y, Luma([pixel_value]));
        }
    }

    // Save the heightmap to the specified file
    img.save(output).expect("Failed to save image");
    println!("Heightmap saved to {}", output);
}
