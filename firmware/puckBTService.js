
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
        description: 'B',
        notify: true,
        readable: true,
        value: new Int32Array([0, 0, 0]).buffer,
    },
  }
},{advertise:[0xBCDE], uart:true});
}


onInit();
