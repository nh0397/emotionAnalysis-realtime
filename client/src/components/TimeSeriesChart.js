import React, { useRef, useEffect, useState } from "react";
import * as d3 from "d3";
import "./TimeSeriesChart.css";

const TimeSeriesChart = ({ dimensions, data, states, selectedState }) => {
  const svgRef = useRef(null);
  const { width, height, margin } = dimensions;
  

  const bandColors = ["#c6dbef", "#9ecae1", "#6baed6", "#3182bd", "#08519c"];
  const emotions = ["anger", "fear", "sadness", "surprise", "joy", "anticipation", "trust"];

  const allStates = Array.from(states);
  const [currentState, setCurrentState] = useState(selectedState);
  const [selectedEmotion, setSelectedEmotion] = useState(emotions[0]);
  const [activeTab, setActiveTab] = useState(1);
  const [selectedState1, setSelectedState1] = useState(allStates[0]);
  const [selectedState2, setSelectedState2] = useState(allStates[1]);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    if (activeTab === 3) {
      const state1Data = data.filter((d) => d.state === selectedState1);
      const state2Data = data.filter((d) => d.state === selectedState2);
  
      const reducedHeight = height / 3; // Reduce the height of each graph
  
      svg.attr("width", width + margin.left + margin.right)
        .attr("height", reducedHeight * 2 + margin.top + margin.bottom + 40);
  
      const tooltip = d3.select("body").append("div")
        .attr("class", "tooltip")
        .style("opacity", 0);
  
      const xScale = d3.scaleTime()
        .domain(d3.extent(data, (d) => new Date(d.date)))
        .range([0, width]);
  
      const yScale = d3.scaleLinear()
        .domain([-0.2, 0.2])
        .range([reducedHeight, 0]); // Use reducedHeight for scaling
  
      const chartGroup = svg.append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top})`);
  
      // Draw Y-Axis first (to ensure visibility)
      chartGroup.append("g")
        .call(d3.axisLeft(yScale).tickValues([-0.2, -0.1, 0, 0.1, 0.2]).tickFormat((d) => d.toFixed(1)))
        .style("z-index", 10) // Ensures it’s on top of other elements
        .selectAll("text")
        .style("font-size", "10px")
        .style("font-weight", "bold");
  
      // Horizon chart for state1 (above x-axis)
      bandColors.forEach((color, i) => {
        chartGroup.append("path")
          .datum(state1Data)
          .attr("fill", color)
          .attr("d", d3.area()
            .x((d) => xScale(new Date(d.date)))
            .y0((d) => yScale(Math.min(0.2, Math.max(0, d[selectedEmotion] - (i + 1) * 0.2))))
            .y1((d) => yScale(Math.min(0.2, Math.max(0, d[selectedEmotion] - i * 0.2))))
            .curve(d3.curveMonotoneX)
          )
          .on("mouseover", (event, d) => {
            tooltip.transition().duration(200).style("opacity", 0.9);
            tooltip.html(`State: ${selectedState1}<br>Emotion: ${selectedEmotion}<br>Score: ${d[selectedEmotion]}`)
              .style("left", (event.pageX + 5) + "px")
              .style("top", (event.pageY - 28) + "px");
          })
          .on("mouseout", () => tooltip.transition().duration(500).style("opacity", 0));
      });
  
      // Horizon chart for state2 (below x-axis, inverted)
      bandColors.forEach((color, i) => {
        chartGroup.append("path")
          .datum(state2Data)
          .attr("fill", color)
          .attr("d", d3.area()
            .x((d) => xScale(new Date(d.date)))
            .y0((d) => yScale(-Math.min(0.2, Math.max(0, d[selectedEmotion] - i * 0.2))))
            .y1((d) => yScale(-Math.min(0.2, Math.max(0, d[selectedEmotion] - (i + 1) * 0.2))))
            .curve(d3.curveMonotoneX)
          )
          .on("mouseover", (event, d) => {
            tooltip.transition().duration(200).style("opacity", 0.9);
            tooltip.html(`State: ${selectedState2}<br>Emotion: ${selectedEmotion}<br>Score: ${d[selectedEmotion]}`)
              .style("left", (event.pageX + 5) + "px")
              .style("top", (event.pageY - 28) + "px");
          })
          .on("mouseout", () => tooltip.transition().duration(500).style("opacity", 0));
      });
  
      // Append X-Axis
      chartGroup.append("g")
        .attr("transform", `translate(0, ${reducedHeight})`)
        .call(d3.axisBottom(xScale).ticks(d3.timeMonth.every(1)).tickFormat(d3.timeFormat("%Y-%m")))
        .selectAll("text")
        .attr("dx", "0.5em")
        .attr("dy", "0.5em")
        .attr("transform", "rotate(30)")
        .style("text-anchor", "start")
        .style("font-size", "8px");
  
      // State Labels
      chartGroup.append("text")
        .attr("x", 10)
        .attr("y", yScale(0.15))
        .text(selectedState1)
        .style("font-size", "12px")
        .style("font-weight", "bold");
  
      chartGroup.append("text")
        .attr("x", 10)
        .attr("y", yScale(-0.15))
        .text(selectedState2)
        .style("font-size", "12px")
        .style("font-weight", "bold");
  
      return () => tooltip.remove();
    }

    const isTab1 = activeTab === 1;
    const chartItems = isTab1 ? emotions : allStates;
    const rowHeight = 100;
    const verticalPadding = 50;

    svg.attr("width", width + margin.left + margin.right)
      .attr("height", chartItems.length * (rowHeight + verticalPadding) + margin.top + margin.bottom);

    const tooltip = d3.select("body").append("div")
      .attr("class", "tooltip")
      .style("opacity", 0);

    chartItems.forEach((item, index) => {
      const chartData = isTab1
        ? data.filter(d => d.state === currentState)
        : data.filter(d => d.state === item);

      const xScale = d3.scaleTime()
        .domain(d3.extent(chartData, d => new Date(d.date)))
        .range([0, width]);

      const yScale = d3.scaleLinear()
        .domain([0, 0.2])
        .range([rowHeight, 0]);

      const chartGroup = svg.append("g")
        .attr("transform", `translate(${margin.left}, ${index * (rowHeight + verticalPadding) + margin.top})`);

      // X-Axis
      chartGroup.append("g")
        .attr("transform", `translate(0, ${rowHeight})`)
        .call(d3.axisBottom(xScale).ticks(d3.timeMonth.every(1)).tickFormat(d3.timeFormat("%Y-%m")))
        .selectAll("text")
        .attr("dx", "0.5em")
        .attr("dy", "0.5em")
        .attr("transform", "rotate(30)")
        .style("text-anchor", "start")
        .style("font-size", "8px")

      // Y-Axis
      chartGroup.append("g")
        .call(d3.axisLeft(yScale).tickValues([0, 0.1, 0.2]).tickFormat(d => d.toFixed(1)))
        .selectAll("text")
        .style("font-size", "8px")
        .style("z-index", "2");

      // Horizon chart layers
      bandColors.forEach((color, i) => {
        chartGroup.append("path")
          .datum(chartData)
          .attr("fill", color)
          .attr("d", d3.area()
            .x(d => xScale(new Date(d.date)))
            .y0(d => yScale(Math.min(0.2, Math.max(0, (isTab1 ? d[item] : d[selectedEmotion]) - (i + 1) * 0.2))))
            .y1(d => yScale(Math.min(0.2, Math.max(0, (isTab1 ? d[item] : d[selectedEmotion]) - i * 0.2))))
            .curve(d3.curveMonotoneX)
          )
          .on("mouseover", (event, d) => {
            tooltip.transition().duration(200).style("opacity", 0.9);
            tooltip.html(isTab1
              ? `State: ${currentState}<br>Emotion: ${item}<br>Score: ${d[item]}`
              : `State: ${item}<br>Emotion: ${selectedEmotion}<br>Score: ${d[selectedEmotion]}`
            )
              .style("left", (event.pageX + 5) + "px")
              .style("top", (event.pageY - 28) + "px");
          })
          .on("mouseout", () => tooltip.transition().duration(500).style("opacity", 0));
      });

      // Chart Label
      chartGroup.append("text")
        .attr("x", -margin.left)
        .attr("y", -5)
        .text(isTab1 ? item.charAt(0).toUpperCase() + item.slice(1) : item)
        .style("font-size", "10px")
        .attr("fill", "black")
        .style("font-weight", "bold");
    });

    return () => tooltip.remove();

  }, [activeTab, currentState, selectedEmotion, selectedState1, selectedState2, data, margin, width, height]);

  return (
    <div>
      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab-button ${activeTab === 1 ? "active" : ""}`}
          onClick={() => setActiveTab(1)}
        >
          Emotions across a state
        </button>
        <button
          className={`tab-button ${activeTab === 2 ? "active" : ""}`}
          onClick={() => setActiveTab(2)}
        >
          One emotion across all states
        </button>
        <button
          className={`tab-button ${activeTab === 3 ? "active" : ""}`}
          onClick={() => setActiveTab(3)}
        >
          Two state comparison
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 1 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <select
            className="state-dropdown"
            value={currentState}
            onChange={(e) => setCurrentState(e.target.value)}
          >
            {allStates.map((state) => (
              <option key={state} value={state}>
                {state}
              </option>
            ))}
          </select>
          <div
            style={{
              maxHeight: "600px", // Set the height for the scrollable container
              overflowY: "auto", // Enable vertical scrolling
              border: "1px solid #ccc",
              padding: "10px"
            }}
          >
            <svg ref={svgRef}></svg>
          </div>
        </div>
      )}
      {activeTab === 2 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <select
            className="state-dropdown"
            value={selectedEmotion}
            onChange={(e) => setSelectedEmotion(e.target.value)}
          >
            {emotions.map((emotion) => (
              <option key={emotion} value={emotion}>
                {emotion.charAt(0).toUpperCase() + emotion.slice(1)}
              </option>
            ))}
          </select>
          <div
            style={{
              maxHeight: "600px", // Set the height for the scrollable container
              overflowY: "auto", // Enable vertical scrolling
              border: "1px solid #ccc",
              padding: "10px"
            }}
          >
            <svg ref={svgRef}></svg>
          </div>
        </div>
      )}
      {activeTab === 3 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px", alignItems: "center" }}>
          <div style={{ display: "flex", flexDirection: "row", gap: "10px" }}>
            <select
              className="state-dropdown"
              value={selectedState1}
              onChange={(e) => setSelectedState1(e.target.value)}
            >
              {allStates.map((state) => (
                <option key={state} value={state}>
                  {state}
                </option>
              ))}
            </select>
            <select
              className="state-dropdown"
              value={selectedState2}
              onChange={(e) => setSelectedState2(e.target.value)}
            >
              {allStates.map((state) => (
                <option key={state} value={state}>
                  {state}
                </option>
              ))}
            </select>
            <select
            className="state-dropdown"
            value={selectedEmotion}
            onChange={(e) => setSelectedEmotion(e.target.value)}
            style={{ marginLeft: "auto" }}
          >
            {emotions.map((emotion) => (
              <option key={emotion} value={emotion}>
                {emotion.charAt(0).toUpperCase() + emotion.slice(1)}
              </option>
            ))}
          </select>
          </div>
          <div
            style={{
              maxHeight: "900px",
              overflowY: "auto",
              border: "1px solid #ccc",
              padding: "10px",
              width: "100%",
            }}
          >
            <svg ref={svgRef}></svg>
          </div>
        </div>
      )}
    </div>
  );
};

export default TimeSeriesChart;
