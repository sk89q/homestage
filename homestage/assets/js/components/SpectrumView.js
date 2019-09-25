import React from "react";
import {observer} from "mobx-react";

@observer
export class SpectrumBar extends React.Component {
  render() {
    return (
      <div className="spectrum-bar" style={{height: (this.props.value * 100) + '%'}}>
      </div>
    );
  }
}

@observer
export default class extends React.Component {
  render() {
    return (
      <div className="spectrum">
        {this.props.controller.spectrumAdjusted.map((value, index) => <SpectrumBar key={index} value={value}/>)}
      </div>
    );
  }
}
