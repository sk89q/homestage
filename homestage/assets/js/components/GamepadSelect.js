import React from "react";
import {observer} from "mobx-react";
import Select from 'react-select';

@observer
export default class extends React.Component {
  setChoice = choice => {
    this.props.controller.setGamepad(choice);
  };

  mapChoice(entry) {
    return entry ? {
      value: entry.id,
      label: entry.id,
    } : null;
  }

  render() {
    const options = this.props.controller.gamepads.filter(o => o).map(this.mapChoice);
    const value = this.mapChoice(this.props.controller.gamepad);

    return (
      <Select
        value={value}
        onChange={this.setChoice}
        options={options}
      />
    );
  }
}
