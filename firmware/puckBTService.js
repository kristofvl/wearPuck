
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
            value: new Float32Array([xyz.acc.x, xyz.acc.y, xyz.acc.z]).buffer,
            notify: true
          },
          0xB000: {
            value: new Float32Array([xyz.gyro.x, xyz.gyro.y, xyz.gyro.z]).buffer,
            notify: true
          }
        }
      });
      messages += 1;
  }
});

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
          0xC000: {
            value: new Float32Array([temp_act, press_act, hum_act]).buffer,
            notify: true
          },
        }
      });
      messages += 1;
  }
}


Puck.accelOn(12.5);

function onInit() {
  NRF.on('connect', function () {
      connected = true;
      //Puck.ioWr(0x80,0);
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
        description: 'Puck Acceleration',
        notify: true,
        readable: true,
        value: new Float32Array([0, 0, 0]).buffer,
    },
    0xB000 : {
        description: 'Puck Gyroscope',
        notify: true,
        readable: true,
        value: new Int32Array([0, 0, 0]).buffer,
    },
    0xC000 : {
        description: 'ATmosphere',
        notify: true,
        readable: true,
        value: new Int32Array([0, 0, 0]).buffer,
    },
  }
},{advertise:[0xBCDE], uart:true});
}


onInit();

var read_int = setInterval(readBME, 1000);  // read every 5 seconds
