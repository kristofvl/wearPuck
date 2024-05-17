const debug = true;

// https://www.espruino.com/BME280 
I2C1.setup({scl:D2,sda:D1});
var bme = require("BME280").connect(I2C1);

function fPad(f,s) {  // kvl, pad a float to ± 5 digits left, 2 right
  return (s?(f<0?'-':'+'):'')+Math.abs(f).toFixed(2).padStart(5,'0');
}

function readBME() {  // kvl, read single package & output to console
  bme.readRawData();
  var temp_cal = bme.calibration_T(bme.temp_raw);
  var press_cal = bme.calibration_P(bme.pres_raw);
  var hum_cal = bme.calibration_H(bme.hum_raw);
  var temp_act = temp_cal / 100.0;
  var press_act = press_cal / 100.0;
  var hum_act = hum_cal / 1024.0;
  if (debug)
      console.log(fPad(press_act,0) + "hPa, "
              + fPad(temp_act,1) + "C, "
              + fPad(hum_act,0)+"%");
}

Puck.accelOn(12.5);

Puck.on('accel', function(d) {
  // read IMU data:
  if (debug)
    console.log(d.acc.x + " " + d.acc.y + " " + d.acc.z + " " 
                + d.gyro.x + " " + d.gyro.y + " " + d.gyro.z);
});

var read_int = setInterval(readBME, 5000);  // read every 5 seconds
