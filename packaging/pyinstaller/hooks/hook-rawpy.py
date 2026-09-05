from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs

datas, binaries, hiddenimports = collect_all("rawpy")
binaries += collect_dynamic_libs("rawpy")
hiddenimports += ["_rawpy"]
