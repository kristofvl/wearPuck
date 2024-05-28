
// https://www.espruino.com/BME280 
I2C1.setup({scl:D2,sda:D1});
var bme = require("BME280").connect(I2C1);



var connected = false;
var messages = 0;

function mSplit(num) {

    // Get the lower 16 bits
    const lower16Bits = num & 0xFFFF;

    // Get the upper 16 bits by shifting right 16 bits
    const upper16Bits = (num >>> 16) & 0xFFFF;

    return {
        up: upper16Bits,
        low: lower16Bits
    };
}



Puck.on('accel', function(xyz) {
  if (connected) {
    mRet = mSplit(messages);
    NRF.updateServices({
      0xBCDE: {
        0xA000: {
          value: new Int16Array([xyz.acc.x, xyz.acc.y, xyz.acc.z, xyz.gyro.x, xyz.gyro.y, xyz.gyro.z, mRet.up, mRet.low]).buffer,
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
  if (connected) {
    mRet = mSplit(messages);
    NRF.updateServices({
      0xBCDE: {
        0xB000: {
          value: new Int16Array([temp_cal, press_cal, hum_cal, mRet.up, mRet.low]).buffer,
          notify: true
        },
      }
    });
    updateTimestamp();
  }
}


Puck.accelOn(52);

function onInit() {
  NRF.on('connect', function () {
      connected = true;
  });
  NRF.on('disconnect', function () {
      connected = false;
  });
  NRF.setServices({
  0xBCDE : {
    0xA000 : {
        description: 'Puck Acc Gyro',
        notify: true,
        readable: true,
        value: new Int16Array([0, 0, 0, 0, 0, 0, 0, 0]).buffer,
    },
    0xB000 : {
        description: 'Atmosphere',
        notify: true,
        readable: true,
        value: new Int16Array([0, 0, 0, 0, 0]).buffer,
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
        value: new Int16Array([0, 0, 0]).buffer,
    },
    0xE000: {
      description: "timestamps",
      notify: true,
      readable : true,
      value: new Float64Array([0, 0]).buffer,
    },
    0xF000: {
      description: "capacitive",
      notify: true,
      readable : true,
      value: new Int32Array([0, 0]).buffer,
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
    /*devs.foreach(function(dev) { // not working yet, need a different loop type
      if (dev.manufaturer == 0x590) {
        mRet = mSplit(messages);
        NRF.updateServices({
          0xBCDE: {
            0xD000: {
              value: new Int16Array([dev.rssi, mRet.up, mRet.low]).buffer,
              notify: true
            },
          }
        });
        updateTimestamp();
      }
    });*/
  }, 2000);
}

function readCap() {
  if (!connected) return;
  var cap_val = Puck.capSense();
  mRet = mSplit(messages);
  NRF.updateServices({
    0xBCDE: {
      0xF000: {
        value: new Int32Array([cap_val, messages]).buffer,
        notify: true
      },
    }
  });
  updateTimestamp();
}

var read_cap = setInterval(readCap, 1000);

var read_ble = setInterval(readBeacon, 5000);
