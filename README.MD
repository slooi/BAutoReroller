

# How to Setup
- This guide assmumes you will be using version 3.3.1 and Windows, but similar steps should be applicable for other platforms

1. Download `scrcpy.zip` or the tar file for your platform: https://github.com/Genymobile/scrcpy/releases/tag/v3.3.1
2. Also download the `scrcpy-server` (eg:`scrcpy-server-v3.3.1`)
3. Extract your `scrcpy.zip` file. There should be a `scrcpy.exe` inside
4. Move your `scrcpy-server` into the extracted folder so it's in the same dir as the `scrcpy.exe`
5. Open a terminal in this directory
6. Get your Android phone & go into `settings>developer mode`. 
7. Scroll down and tap on wireless debugging to open up the wireless debug window. Then turn on wireless debugging and note your ip & port for the next step. 
8. In your terminal and enter `adb pair IP_AND_PORT`. Replace `IP_AND_PORT` with your ip and port. You should be prompted on your phone, accept it.
9. Run `adb connect IP_AND_PORT_2`. This should be the same IP of your device but the port should be different.
10. Run `adb devices`, you should see your device listed
11. Now run the below commands to run the scrcpy server on your phone
```sh
adb push scrcpy-server-v3.3.1 /data/local/tmp/scrcpy-server-manual.jar

adb forward tcp:1234 localabstract:scrcpy

adb shell CLASSPATH=/data/local/tmp/scrcpy-server-manual.jar app_process / com.genymobile.scrcpy.Server 3.3.1 tunnel_forward=true audio=false control=false cleanup=false raw_stream=true max_size=1920
```
12. Now in a different terminal git clone this repo and cd into it
13. Then run `python main.py` to connect to the server and render the video display
14. DONE! :D