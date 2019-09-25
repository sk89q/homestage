import {computed, observable} from "mobx";
import openSocket from 'socket.io-client'

function buttonPressed(b) {
  if (typeof (b) == "object") {
    return b.pressed;
  }
  return b === 1.0;
}

export default class {
  @observable connected = false;
  @observable microphones = [];
  @observable microphone = null;
  @observable gamepads = [];
  @observable gamepadIndex;
  @observable enabled = false;
  @observable spectrumAdjusted = [];
  @observable currentTempo = 0;
  @observable beat = false;
  @observable media = null;
  animationFrameRequestId;
  socket;
  lastSendTime = 0;
  updateInterval = 10;

  @computed
  get gamepad() {
    return this.gamepads[this.gamepadIndex];
  }

  constructor() {
    this.loop();

    this.socket = openSocket();

    this.socket.on('status', this.update);

    this.socket.on('connect', () => {
      this.socket.emit('initialize', {});
      this.connected = true;
    });

    this.socket.on('disconnect', () => {
      this.connected = false;
    });
  }

  setGamepad(gamepad) {
    if (gamepad) {
      for (let i = 0; i < this.gamepads; i++) {
        if (this.gamepads[i] && this.gamepads[i].id === gamepad.value) {
          this.gamepadIndex = i;
          return;
        }
      }
    }
    this.gamepadIndex = null;
  }

  setMicrophone(microphone) {
    this.socket.emit('setmicrophone', microphone);
  }

  _sendUpdate() {
    if (!this.socket) {
      return;
    }

    if (this.gamepad) {
      this.socket.emit('setcontrol', {
        axis0: [this.gamepad.axes[0], this.gamepad.axes[1]],
        axis1: [this.gamepad.axes[2], this.gamepad.axes[3]],
        lb: buttonPressed(this.gamepad.buttons[4]),
        rb: buttonPressed(this.gamepad.buttons[5]),
        lt: this.gamepad.buttons[6].value,
        rt: this.gamepad.buttons[7].value,
        left: buttonPressed(this.gamepad.buttons[14]),
        right: buttonPressed(this.gamepad.buttons[15]),
        up: buttonPressed(this.gamepad.buttons[12]),
        down: buttonPressed(this.gamepad.buttons[13]),
        triangle: buttonPressed(this.gamepad.buttons[3]),
        square: buttonPressed(this.gamepad.buttons[2]),
        circle: buttonPressed(this.gamepad.buttons[1]),
        cross: buttonPressed(this.gamepad.buttons[0]),
      });
    } else {
      this.socket.emit('poll', {});
    }
  }

  loop = () => {
    try {
      const now = performance.now();

      if (now - this.lastSendTime > this.updateInterval) {
        const gamepads = navigator.getGamepads ? Array.from(navigator.getGamepads()) : (Array.from(navigator.webkitGetGamepads) ? navigator.webkitGetGamepads : []);
        this.gamepads = gamepads ? gamepads : [];

        if (!this.gamepadIndex || !this.gamepads[this.gamepadIndex]) {
          for (let i = 0; i < this.gamepads.length; i++) {
            if (this.gamepads[i]) {
              this.gamepadIndex = i;
              break;
            }
          }
        }

        this._sendUpdate();
      }

      this.lastSendTime = now;
    } finally {
      this.animationFrameRequestId = requestAnimationFrame(this.loop);
    }
  };

  update = data => {
    for (const key of Object.keys(data)) {
      this[key] = data[key];
    }
  };
}
