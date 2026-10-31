name: build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - uses: actions/setup-java@v5
        with:
          distribution: 'temurin'
          java-version: '21'
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.27.4'
      - run: pip install flet==0.28.3
      - run: flet build apk --verbose
      - uses: actions/upload-artifact@v4
        with:
          name: Volume-King-APK
          path: build/apk
