# Android APK

The application embeds the same standalone HTML used by the desktop builds and runs it in Android System WebView. It supports Android 8.0 (API 26) and later with WebView or Chrome version 109 or later for MathML. The manifest requests no permissions. The system document picker opens XYZ structures and loads or saves JSON projects. Results can be copied to the clipboard. The application ID is `io.github.lightzfpwings.basischaracter`.

From the integrated module directory, build with JDK 17 or newer and the Android SDK.

```sh
sdkmanager "platforms;android-35" "build-tools;35.0.0"
python3 packaging/build_android.py
```

The build produces an aligned universal unsigned APK and an APK validation report in `dist/`. Sign the APK with the persistent application keystore and verify the certificate fingerprint against the signing record. Keep that keystore for future updates of the same package.

```sh
apksigner sign --ks /path/to/release.p12 --ks-type PKCS12 --ks-key-alias basis-release \
  --v4-signing-enabled false --out dist/BasisCharacter-0.5.0-Android.apk \
  dist/BasisCharacter-0.5.0-Android-unsigned.apk
apksigner verify --verbose --print-certs dist/BasisCharacter-0.5.0-Android.apk
```

For the runtime smoke test, use a Linux runner with KVM available or another host with an accelerated API 35 emulator. The test installs ephemeral test-signed APKs in a disposable emulator, launches the normal app, calculates the two water SALCs, checks the clipboard and round-trips the exported JSON through Android content URIs. It also checks formula selection, IR/Raman activity, the XYZ file picker and mobile layout. Instrumentation supplies the document-picker choices. It leaves the release candidate unsigned for the private signing step.

```sh
sdkmanager "platform-tools" "emulator" "system-images;android-35;google_apis;x86_64"
echo no | avdmanager create avd -n basis-smoke -k "system-images;android-35;google_apis;x86_64" --force
python3 packaging/build_android.py --smoke --avd basis-smoke
```
