import React from 'react'
import ReactDOM from 'react-dom'
import Controller from './model/Controller'
import MonitorView from './components/MonitorView'
import 'bootstrap'

const controller = new Controller();
ReactDOM.render(<MonitorView controller={controller}/>, document.getElementById('view'));
