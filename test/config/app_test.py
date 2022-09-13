import os

import app.config.app


def test_config():
    assert app.config.app.settings.Config.env_file is not None
