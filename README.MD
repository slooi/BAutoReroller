# BAutoReroller
An Android auto reroller for Blue Archive


# How to Setup
- This guide assumes you will be using scrcpy version 3.3.1 and Windows, but similar steps should be applicable for mac & linux

1. Download `scrcpy.zip` or the tar file for your platform: https://github.com/Genymobile/scrcpy/releases/tag/v3.3.1
2. Also download the `scrcpy-server` (eg:`scrcpy-server-v3.3.1`)
3. Extract your `scrcpy.zip` file. There should be a `scrcpy.exe` inside
4. Move your `scrcpy-server` into the extracted folder so it's in the same dir as the `scrcpy.exe`
5. Open a terminal in this directory
6. Get your Android phone & navigate into `Settings>Developer options`. 
7. Scroll down and tap on wireless debugging to open up additional wireless debugging settings. A new window should appear.
8. Then tap on `Pair device with pairing code`. A code, IP and port should appear which we will use for the next step.
9. In your terminal and enter `adb pair IP:PORT`. Replace `IP:PORT` with the ip and port shown previously. You should be prompted on your phone, accept it.
10. Run `adb connect IP:PORT_2`. This should be the same IP of your device but the port should be different.
11. Run `adb devices`, you should see your device listed
12. Now run the below commands
```sh
adb push scrcpy-server-v3.3.1 /data/local/tmp/scrcpy-server-manual.jar

adb forward tcp:1234 localabstract:scrcpy

adb shell CLASSPATH=/data/local/tmp/scrcpy-server-manual.jar app_process / com.genymobile.scrcpy.Server 3.3.1 tunnel_forward=true audio=false control=false cleanup=false raw_stream=true max_size=1920
```
13. Now in a different terminal git clone this repo, `cd` into it, then run `pip install -r requirements.txt`
14. Then run `python main.py` to connect and render your phone's display
15. DONE! :D