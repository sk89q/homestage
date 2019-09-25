import React from "react";
import {observer} from "mobx-react";
import MicrophoneSelect from "./MicrophoneSelect";
import GamepadSelect from "./GamepadSelect";
import SpectrumView from "./SpectrumView";

@observer
export default class extends React.Component {
  render() {
    return (
      <div className="stage">
        <div className="d-flex flex-column">
          <div className="d-flex align-items-center stage-card">
            <div className="mr-2">
              Audio:
            </div>
            <div className="flex-grow-1 mr-1">
              <MicrophoneSelect controller={this.props.controller}/>
            </div>
            <div className="ml-2 mr-2">
              Control:
            </div>
            <div className="flex-grow-1 ml-1">
              <GamepadSelect controller={this.props.controller}/>
            </div>
          </div>
          <div className="mt-2 stage-card">
            <span
              className={`badge badge-pill badge badge-pill mr-1 badge-${this.props.controller.connected ? 'success' : 'danger'}`}>
              Connected
            </span>
            <span className={`badge badge-pill mr-1 badge-${this.props.controller.enabled ? 'success' : 'danger'}`}>
              Enabled
            </span>
            <span className={`badge badge-pill mr-1 badge-${this.props.controller.beat ? 'info' : 'secondary'}`}>
              Beat
            </span>
          </div>
          <div className="mt-2 stage-card">
            Tempo: {Math.round(this.props.controller.currentTempo)} beats/minute
          </div>
          <div className="mt-2 stage-card">
            <SpectrumView controller={this.props.controller}/>
          </div>
        </div>
      </div>
    );
  }
}
