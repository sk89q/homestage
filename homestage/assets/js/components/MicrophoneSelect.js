import React from "react";
import {observer} from "mobx-react";
import Select from 'react-select';

@observer
export default class extends React.Component {
  setChoice = choice => {
    this.props.controller.setMicrophone(choice);
  };

  render() {
    return (
      <Select
        value={this.props.controller.microphone}
        onChange={this.setChoice}
        options={this.props.controller.microphones}
      />
    );
  }
}
