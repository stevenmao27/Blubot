# Notes on Manual Configuration

### Actual Dependency Requirements

`pip install [dependency]`

- `py-cord`
- `requests`
- `youtube-dl`
- `python-dotenv`

\

Make sure the application `ffmpeg` is downloaded as well.

For Windows:

- go to `https://www.gyan.dev/ffmpeg/builds/`
- install `ffmpeg-git-essentials.7z` from the git master branch build
- extract the folder with 7z and put it in desired location; I will put the folder directly in C:\ drive (and will rename to simply ffmpeg)
- go to windows start and type `environment variables` to open `edit the system environment variables`
- go to `environment variables...`
- scroll down `system variables` list until you find the variable `Path`
- click `Edit...` then `New`
- type the **absolute path** of the ffmpeg executable *folder* aka "bin". Since I put the downloaded folder in the C:\ drive, the path is `C:\ffmpeg\bin`
- verify that ffmpeg was installed correctly:
  - open cmd or powershell
  - type `ffmpeg -version` or just `ffmpeg`, and you should get some non-error response.
