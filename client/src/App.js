import './App.css';
import React, { Component } from 'react';
import DotPlotchart1 from './views/DotPlotChart1';
import Navbar from './components/Navbar/Navbar';
const dimensions = {
  width: 1000,
  height: 900,
  margin: { top: 30, right: 350, bottom: 60, left: 300 }
};

const emotionColorsObjects = [
  { emotion: 'anger', color: '#FF0000' },
  { emotion: 'fear', color: '#FFA500' },
  { emotion: 'positive', color: '#008000' },
  { emotion: 'sadness', color: '#0000FF' },
  { emotion: 'surprise', color: '#FFC0CB' },
  { emotion: 'joy', color: '#FFD700' },
  { emotion: 'anticipation', color: '#9400D3' },
  { emotion: 'trust', color: '#00FFFF' },
  { emotion: 'negative', color: '#A9A9A9' },
  { emotion: 'disgust', color: '#808000' }
];

class App extends Component {

  constructor(props) {
    super(props);
    this.state = { data: [], timeSeriesData:[] };
  }

  componentDidMount() {
    console.log("In component did mount");
    this.callBackendAPI()
      .then(data => this.setState({ data: data }))
      .catch(err => console.log(err));

      this.getTimeSeriesData()
      .then(data => this.setState({ timeSeriesData: data }))
      .catch(err => console.log(err));
  }
  

  
  callBackendAPI = async () => {
    const response = await fetch('http://localhost:9000/data');
    const body = await response.json();

    if (response.status !== 200) {
      throw Error(body.message)
    }
    return body;
  };

  getTimeSeriesData = async () => {
    const response = await fetch('http://localhost:9000/timeSeriesData');
    const body = await response.json();

    if (response.status !== 200) {
      throw Error(body.message)
    }
    return body;
  };


  render() {
    const { data, selectedItems } = this.state;
    return (
      <div className="App" >
        <Navbar/>
        <>
          <DotPlotchart1
            data={data}
            timeSeriesData={this.state.timeSeriesData}
            dimensions={dimensions}
            selectedItems={selectedItems}
            colorObjects={emotionColorsObjects}
          />
        </>
      </div>
    );
  }
}

export default App;
