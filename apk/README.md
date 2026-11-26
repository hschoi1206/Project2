# 안드로이드 앱(APK) 빌드

`cycle/` 웹앱을 [Capacitor](https://capacitorjs.com/)로 감싸 APK를 만듭니다. 기록은 앱 전용 저장공간에 저장되므로 크롬 데이터를 지워도 영향을 받지 않습니다. (앱 삭제나 "설정 → 앱 → 데이터 삭제"는 기록도 지웁니다.)

- 앱 ID: `io.github.hschoi1206.cycle`
- 버전: `package.json`의 `version` (versionName으로 들어감)
- 빌드: GitHub Actions `.github/workflows/android-apk.yml`
  - `cycle/`나 `apk/`가 바뀌어 push되면 빌드를 확인합니다.
  - Actions 탭 → **Android APK** → **Run workflow**를 누르면 서명된 APK를 Release `v<버전>`에 올립니다.
- 서명: 저장소 Secrets `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD` (키 별칭 `weight`, 체중 앱과 같은 키). 업데이트하려면 같은 키로 서명해야 하므로 키를 바꾸지 마세요.

## 웹 버전에서 기록 옮기기
웹 버전과 APK는 저장공간이 따로입니다. 웹 버전에서 **⬇ 백업 내보내기** → APK에서 **⬆ 백업 불러오기**.

## 새 버전 내는 법
1. `cycle/` 수정
2. `apk/package.json`의 `version`과 `cycle/index.html`의 `APP_VERSION`을 올림 (예: 1.0.1)
3. Actions에서 **Run workflow** → Release에서 새 APK를 받아 설치(기존 앱 위에 덮어쓰기, 기록 유지)
