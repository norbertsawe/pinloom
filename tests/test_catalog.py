"""Regression checks on physical pins where previous diagrams were misleading."""


def pins(db, key):
    return {p.number: p for p in db.exact(key).pins}


def test_pico_spi_direction_and_power(db):
    p = pins(db, "pico")
    assert "SPI0 RX (MISO)" in p["21"].functions
    assert "SPI0 SCK" in p["24"].functions
    assert "SPI0 TX (MOSI)" in p["25"].functions
    assert p["33"].kind == "ground"
    assert p["36"].name == "3V3"
    assert p["40"].name == "VBUS"


def test_expander_package_and_audio_dac(db):
    p = pins(db, "mcp23017")
    assert p["9"].name == "VDD"
    assert p["10"].kind == "ground"
    assert p["12"].name == "SCL"
    assert p["13"].name == "SDA"
    assert p["18"].name == "/RESET"
    p = pins(db, "pcm5102a")
    assert p["3"].kind == "ground"
    assert p["6"].name == "OUTL"
    assert p["13"].name == "BCK"
    assert p["15"].name == "LRCK"
    assert p["18"].name == "LDOO"
    assert p["20"].name == "DVDD"


def test_uno_nano_and_bare_avr_are_distinct(db):
    assert len(db.exact("atmega328p").pins) == 28
    assert len(db.exact("nano").pins) == 30
    assert "SPI MOSI" in pins(db, "atmega328p")["17"].functions
    assert "SPI MOSI" in pins(db, "uno")["D11"].functions
    assert pins(db, "nano")["25"].name == "A6"
    assert "Analog input only" in pins(db, "nano")["25"].notes[0]


def test_esp_board_revisions_and_reserved_pins(db):
    assert len(db.exact("esp32").pins) == 38
    assert len(db.exact("esp32s3").pins) == 44
    assert len(db.exact("esp32c3").pins) == 30
    p = pins(db, "esp32")
    assert p["J2.3"].name == "GPIO36"
    assert p["J3.4"].name == "GPIO1"
    assert any("Reserved" in note for note in p["J3.19"].notes)
    assert pins(db, "esp32s3")["J3.19"].name == "GPIO20"
    assert "USB D+" in pins(db, "esp32s3")["J3.19"].functions


def test_nucleo_arduino_connector_ids(db):
    p = pins(db, "nucleo-f401re")
    assert p["CN9.1"].name == "D0"
    assert "PA3" in p["CN9.1"].functions
    assert p["CN5.7"].kind == "ground"
    assert p["CN5.8"].name == "AREF"
    assert p["CN5.9"].name == "D14"
    assert "PB9" in p["CN5.9"].functions
    assert p["CN5.10"].name == "D15"


def test_connector_physical_numbering(db):
    p = pins(db, "raspberry-pi-40")
    assert p["1"].name == "3V3" and p["2"].name == "5V"
    assert "SPI0 MOSI" in p["19"].functions
    assert p["40"].name == "GPIO21"
    p = pins(db, "usb-c")
    assert p["A5"].name == "CC1" and p["B5"].name == "CC2"
    assert p["A6"].name == "D+" and p["B6"].name == "D+"
    assert pins(db, "icsp")["1"].name == "MISO"
    assert pins(db, "swd")["7"].kind == "nc"


def test_amplifier_outputs_and_optocoupler_terminals_are_connected(db):
    for key in ("lm358", "ne5532", "tl072", "mcp6002"):
        p = pins(db, key)
        assert p["1"].name == "OUT A" and p["1"].kind == "analog"
        assert p["7"].name == "OUT B" and p["7"].kind == "analog"
        assert p["2"].name == "IN- A" and p["3"].name == "IN+ A"
    assert pins(db, "lm741")["6"].name == "OUT"
    assert pins(db, "pc817")["1"].name == "ANODE"
    assert pins(db, "pc817")["4"].name == "COLLECTOR"
    assert pins(db, "4n25")["3"].kind == "nc"
    assert pins(db, "4n25")["5"].name == "COLLECTOR"
    assert pins(db, "ams1117-3v3")["2"].kind == "power"


def test_eeprom_family_address_pins_are_variant_specific(db):
    assert db.exact("24lc02b").id == "24lc02"
    assert pins(db, "24lc02")["1"].kind == "nc"
    assert pins(db, "24lc256")["1"].kind == "control"


def test_bilateral_switch_signal_terminals(db):
    p = pins(db, "cd4066")
    assert p["1"].name == "A1" and p["2"].name == "A2"
    assert p["1"].kind == "analog"
    assert p["13"].name == "EN A"
    assert p["7"].kind == "ground"
