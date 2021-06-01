# Wallpaper

Make interesting wallpapers from the pictures you have. Configurable by monitor.

An evolving project that started many moons ago with [this post](https://gabbpuy.blogspot.com/2010/07/set-windows-wallpaper-from-python-for.html)

There was a version on googlecode for a while and other people have created gists on github from it.

This version is gone through some things, it used to also set the login screen on windows when you were able to do that
but since Windows 10 that has been removed again.

I don't use most of the modes any more, I think in particular that `strip` mode right now might have a bug in sizing.

I know how to make this work on a Mac, but I don't have access to one to do the work - it should be easy enough.

It keeps a list of wallpapers in an sqlite db and tries to avoid reusing images for as long as possible, once it can't
find any more images for a given directory it'll clean up the seen ones.

## Using
You can build an exe for it if you install the requirements from `requirements_dev` and run the build_exe.bat - This 
makes it easy to use when you login or on a schedule.

You will need a config file - there's an example in `examples` this is the config I use - I added a monitor section to
show the monitor overrides.

There aren't many requirements - PIL and win32 for windows (wallpapers are more of a pain than you would think).

It will search the current working folder for a `pywallpaper.json` file or you can specify one with `-c`

```shell
usage: wallpaper.py [-h] [--image SINGLE_IMAGE] [--directory DIRECTORIES]
                    [--config CONFIG_FILE] [--working-dir CWD]
                    [--single_image SINGLE_IMAGE]

optional arguments:
  -h, --help            show this help message and exit
  --image SINGLE_IMAGE, -i SINGLE_IMAGE
                        Set wallpaper to this image and exit (overrides -d)
  --directory DIRECTORIES, -d DIRECTORIES
                        Add an image directory
  --config CONFIG_FILE, -c CONFIG_FILE
                        path to alternate config file (default <working
                        dir>/pywallpaper.conf)
  --working-dir CWD, -w CWD
                        Working Directory (default .)
  --single_image SINGLE_IMAGE
                        single image to set as wallpaper
```

These are mostly ignored in favour of the json configuration

### Config

Every item can be defaulted in the `global_config` section and repeated with different settings in the `monitors` section

**blending** If `true` blends each new wallpaper to the previous

**blend_ratio** The amount of blending to use

**crop** Just chop off wallpapers that are too large

**fill** Expand wallpapers to fill the available space

**gradient** Generate a gradient (useful for blending to)

**pre_rotate** If true rotate images based on the aspect ratio of the space being filled

**fill_mode** There are different methods of filling the screen, `swatch`, `spiral` and `strip`

**stop_threshold** Once image dimensions become smaller than this, stop

**spanning** If `true` treat the entire screen space as a single monitor

**single_folder_mode** If `true` fill a space as much as possible from the chosen folder - otherwise choose images at random from anywhere

**stack_mode** If `true` blur the current background and layer the new wallpaper over the top by leaving gaps

**directories** List of directories to look for images - prefix path with a `+` to recurse all subdirectories

**desktop_filters** List of filters to apply to the desktop once rendered

**image_filters** List of filters to apply to each individual image

**background_filters** List of filters to apply to the background once blurred

**monitors** A section with overrides from above keyed by the monitor number starting at `1`

### Wallpaper Library
TBD
