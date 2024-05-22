
// https://www.espruino.com/BME280 
I2C1.setup({scl:D2,sda:D1});
var bme = require("BME280").connect(I2C1);



var connected = false;
var batteryInterval = false;
var messages = 0;
var ang = 0;
var position = "RHR";
var position_code = 0;


Puck.on('accel', function(xyz) {
  if (connected) {
    NRF.updateServices({
      0xBCDE: {
        0xA000: {
          value: new Float32Array([xyz.acc.x, xyz.acc.y, xyz.acc.z, xyz.gyro.x, xyz.gyro.y, xyz.gyro.z, messages]).buffer,
          notify: true
        },
      }
    });
    updateTimestamp();
  }
});

function updateTimestamp() {
  if (connected) {
    NRF.updateServices({
      0xBCDE: {
        0xE000: {
          value: new Float64Array([messages, Date.now()]).buffer,
          notify: true
        },
      }
    });
    messages += 1;
  } 
}

function readBME() {  // kvl, read single package & output to console
  bme.readRawData();
  var temp_cal = bme.calibration_T(bme.temp_raw);
  var press_cal = bme.calibration_P(bme.pres_raw);
  var hum_cal = bme.calibration_H(bme.hum_raw);
  var temp_act = temp_cal / 100.0;
  var press_act = press_cal / 100.0;
  var hum_act = hum_cal / 1024.0;
  if (connected) {
    NRF.updateServices({
      0xBCDE: {
        0xB000: {
          value: new Float32Array([temp_act, press_act, hum_act, messages]).buffer,
          notify: true
        },
      }
    });
    updateTimestamp();
  }
}


Puck.accelOn(12.5);

function onInit() {
  NRF.on('connect', function () {
      connected = true;
      Puck.setOptions({"hrmPollInterval": 40});
      Puck.setOptions({"powerSave": false});
      Puck.setPollInterval(40);
      Puck.setHRMPower(true, "spirit");
      Puck.setCompassPower(true, "spirit");

  });
  NRF.on('disconnect', function () {
      connected = false;
      Puck.setHRMPower(false, "spirit");
      Puck.setCompassPower(false, "spirit");

  });
  NRF.setServices({
  0xBCDE : {
    0xA000 : {
        description: 'Puck Acc Gyro',
        notify: true,
        readable: true,
        value: new Float32Array([0, 0, 0, 0, 0, 0, 0]).buffer,
    },
    0xB000 : {
        description: 'Atmosphere',
        notify: true,
        readable: true,
        value: new Float32Array([0, 0, 0, 0]).buffer,
    },
    0xC000 : {
        description: 'Button',
        notify: true,
        readable: true,
        value: new Int32Array([0, 0]).buffer,
    },
    0xD000: {
        description: 'Beacon',
        notify: true,
        readable: true,
        value: new Int32Array([0, 0]).buffer,
    },
    0xE000: {
      description: "timestamps",
      notify: true,
      readable : true,
      value: new Float64Array([0, 0]).buffer,
    },
  },
},{advertise:[0xBCDE], uart:true});
}


onInit();

var read_int = setInterval(readBME, 1000);  // read every 5 seconds


var button = false;
// Send button presses
setWatch(function() {
  button = !button;
  if (connected) {
    NRF.updateServices({
      0xBCDE: {
        0xC000: {
          value: new Int32Array([button, messages]).buffer,
          notify: true
        },
      }
    });
    updateTimestamp();
  }
}, BTN1, { repeat:1, edge:"both", debounce: 20 });


function readBeacon() {
  if (!connected) return;
  NRF.findDevices(function(devs) {
    devs.foreach(function(dev) {
      if (dev.manufaturer == 0x590) {
        NRF.updateServices({
          0xBCDE: {
            0xD000: {
              value: new Int32Array([dev.rssi, messages]).buffer,
              notify: true
            },
          }
        });
        updateTimestamp();
      }
    });
  }, 2000);
}

var read_ble = setInterval(readBeacon, 5000);
