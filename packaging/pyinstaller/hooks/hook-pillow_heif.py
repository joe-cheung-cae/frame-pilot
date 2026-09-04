from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs

datas, binaries, hiddenimports = collect_all("pillow_heif")
binaries += collect_dynamic_libs("pillow_heif")
hiddenimports += ["_pillow_heif"]
