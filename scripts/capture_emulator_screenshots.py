"""Снимки с локального Android-эмулятора через Appium (без pytest)."""

from __future__ import annotations

import time
from pathlib import Path

from appium import webdriver
from appium.options.common import AppiumOptions
from appium.webdriver.common.appiumby import AppiumBy

MEDIA = Path(__file__).resolve().parent.parent / "media"
APP_PACKAGE = "com.trello"
APP_ACTIVITY = "com.trello.home.HomeActivity"
APPIUM_URL = "http://127.0.0.1:4723"


def _shot(driver, name: str) -> None:
    path = MEDIA / name
    driver.get_screenshot_as_file(str(path))
    print(f"saved: {path.name}")


def main() -> None:
    MEDIA.mkdir(parents=True, exist_ok=True)
    options = AppiumOptions()
    options.load_capabilities(
        {
            "platformName": "Android",
            "appium:automationName": "UiAutomator2",
            "appium:deviceName": "emulator-5554",
            "appium:udid": "emulator-5554",
            "appium:appPackage": APP_PACKAGE,
            "appium:appActivity": APP_ACTIVITY,
            "appium:noReset": True,
            "appium:autoGrantPermissions": True,
        }
    )
    driver = webdriver.Remote(APPIUM_URL, options=options)
    try:
        time.sleep(2)
        _shot(driver, "mobile_emulator_launch.png")

        driver.activate_app(APP_PACKAGE)
        time.sleep(3)
        _shot(driver, "mobile_emulator_home.png")

        for locator in (
            (AppiumBy.XPATH, "//*[@text='Boards' or @text='Доски']"),
            (AppiumBy.ACCESSIBILITY_ID, "Boards"),
            (AppiumBy.ACCESSIBILITY_ID, "Доски"),
        ):
            try:
                tab = driver.find_element(*locator)
                if tab.is_displayed():
                    tab.click()
                    time.sleep(2)
                    break
            except Exception:
                continue

        _shot(driver, "mobile_emulator_boards.png")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
