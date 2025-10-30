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
  const [timeSeriesData, setTimeSeriesData] = useState([]);
  const [loadingTimeSeries, setLoadingTimeSeries] = useState(false);
  const [emotionTimeSeriesData, setEmotionTimeSeriesData] = useState([]);
  const [loadingEmotionTimeSeries, setLoadingEmotionTimeSeries] = useState(false);
  const [comparisonData, setComparisonData] = useState([]);
  const [loadingComparison, setLoadingComparison] = useState(false);

  // Function to fetch time series data for a state
  const fetchTimeSeriesData = async (stateCode) => {
    if (!stateCode) return;
    
    setLoadingTimeSeries(true);
    try {
      console.log(`🕒 Fetching time series data for ${stateCode}...`);
      const response = await fetch(`http://localhost:9000/timeSeriesData/${stateCode}`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`❌ API Error: ${response.status} - ${errorText}`);
        throw new Error(`API Error: ${response.status} - ${errorText}`);
      }
      
      const fetchedData = await response.json();
      console.log(`✅ Time series data loaded for ${stateCode}:`, fetchedData);
      
      // Store the fetched data in state
      setTimeSeriesData(fetchedData);
      
    } catch (error) {
      console.error(`❌ Error fetching time series data for ${stateCode}:`, error);
    } finally {
      setLoadingTimeSeries(false);
    }
  };

  // Function to fetch emotion time series data across all states
  const fetchEmotionTimeSeriesData = async (emotion) => {
    if (!emotion) return;
    
    setLoadingEmotionTimeSeries(true);
    try {
      console.log(`🕒 Fetching ${emotion} time series data across all states...`);
      const response = await fetch(`http://localhost:9000/timeSeriesData/emotion/${emotion}`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`❌ API Error: ${response.status} - ${errorText}`);
        throw new Error(`API Error: ${response.status} - ${errorText}`);
      }
      
      const fetchedData = await response.json();
      console.log(`✅ ${emotion} time series data loaded:`, fetchedData);
      
      // Store the fetched data in state
      setEmotionTimeSeriesData(fetchedData);
      
    } catch (error) {
      console.error(`❌ Error fetching ${emotion} time series data:`, error);
    } finally {
      setLoadingEmotionTimeSeries(false);
    }
  };

  // Function to fetch comparison data for two states on a specific emotion
  const fetchComparisonData = async (state1, state2, emotion) => {
    if (!state1 || !state2 || !emotion) return;
    
    setLoadingComparison(true);
    try {
      console.log(`🕒 Fetching comparison data for ${state1} vs ${state2} on ${emotion}...`);
      const response = await fetch(`http://localhost:9000/timeSeriesData/compare/${state1}/${state2}/${emotion}`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`❌ API Error: ${response.status} - ${errorText}`);
        throw new Error(`API Error: ${response.status} - ${errorText}`);
      }
      
      const fetchedData = await response.json();
      console.log(`✅ Comparison data loaded for ${state1} vs ${state2} on ${emotion}:`, fetchedData);
      
      // Store the fetched data in state
      setComparisonData(fetchedData);
      
    } catch (error) {
      console.error(`❌ Error fetching comparison data:`, error);
    } finally {
      setLoadingComparison(false);
    }
  };

  // Auto-fetch time series data when currentState changes
  useEffect(() => {
    if (currentState) {
      fetchTimeSeriesData(currentState);
    }
  }, [currentState]);

  // Auto-fetch emotion time series data when selectedEmotion changes
  useEffect(() => {
    if (selectedEmotion && activeTab === 2) {
      fetchEmotionTimeSeriesData(selectedEmotion);
    }
  }, [selectedEmotion, activeTab]);

  // Auto-fetch comparison data when Tab 3 parameters change
  useEffect(() => {
    if (selectedState1 && selectedState2 && selectedEmotion && activeTab === 3) {
      fetchComparisonData(selectedState1, selectedState2, selectedEmotion);
    }
  }, [selectedState1, selectedState2, selectedEmotion, activeTab]);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // Show loading state
    if (loadingTimeSeries || loadingEmotionTimeSeries || loadingComparison) {
      svg.append("text")
        .attr("x", (width + margin.left + margin.right) / 2)
        .attr("y", (height + margin.top + margin.bottom) / 2)
        .attr("text-anchor", "middle")
        .style("fill", "#ffffff")
        .style("font-size", "16px")
        .text(loadingTimeSeries ? "Loading time series data..." : 
              loadingEmotionTimeSeries ? "Loading emotion data..." : 
              "Loading comparison data...");
      return;
    }

    // If no time series data, show message
    if (timeSeriesData.length === 0 && currentState) {
      svg.append("text")
        .attr("x", (width + margin.left + margin.right) / 2)
        .attr("y", (height + margin.top + margin.bottom) / 2)
        .attr("text-anchor", "middle")
        .style("fill", "#ffffff")
        .style("font-size", "16px")
        .text(`Select a state to view time series data for ${currentState}`);
      return;
    }

    if (activeTab === 3) {
      // Build per-day difference series from API comparisonData
      // comparisonData contains rows per state with {state, date, [emotion]: value}
      const s1 = comparisonData.filter(d => d.state === selectedState1).map(d => ({ date: d.date, v: d[selectedEmotion] }));
      const s2 = comparisonData.filter(d => d.state === selectedState2).map(d => ({ date: d.date, v: d[selectedEmotion] }));
      const byDate = new Map();
      s1.forEach(d => byDate.set(d.date, { date: d.date, s1: d.v, s2: undefined }));
      s2.forEach(d => {
        const e = byDate.get(d.date) || { date: d.date, s1: undefined, s2: undefined };
        e.s2 = d.v; byDate.set(d.date, e);
      });
      const diffSeries = Array.from(byDate.values()).
        filter(d => d.s1 != null && d.s2 != null).
        map(d => ({ date: d.date, diff: +(d.s1 - d.s2).toFixed(4) }));
  
      const reducedHeight = Math.max(220, Math.round(height / 2)); // Taller diff chart for visibility
  
      svg.attr("width", width + margin.left + margin.right)
        .attr("height", reducedHeight + margin.top + margin.bottom + 60);
  
      const tooltip = d3.select("body").append("div")
        .attr("class", "tooltip")
        .style("opacity", 0);
  
      const xScale = d3.scaleTime()
        .domain(d3.extent(diffSeries, (d) => new Date(d.date)))
        .range([0, width]);
  
      const yScale = d3.scaleLinear()
        .domain([-0.25, 0.25])
        .range([reducedHeight, 0]);
  
      const chartGroup = svg.append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top})`);
  
      // Draw Y-Axis first (to ensure visibility)
      const yAxisTicks = [-0.25, -0.2, -0.1, 0, 0.1, 0.2, 0.25];
      chartGroup.append("g")
        .call(d3.axisLeft(yScale).tickValues(yAxisTicks).tickFormat((d) => d.toFixed(2)))
        .style("z-index", 10)
        .selectAll("text")
        .style("font-size", "12px")
        .style("font-weight", "bold");

      // Horizontal grid lines
      chartGroup.append("g")
        .attr("class", "grid")
        .call(
          d3.axisLeft(yScale)
            .tickValues(yAxisTicks)
            .tickSize(-width)
            .tickFormat("")
        )
        .selectAll("line")
        .attr("stroke", "#333")
        .attr("stroke-opacity", 0.4)
        .attr("stroke-dasharray", "2,2");
  
      // Difference area: positive diff above axis, negative below
      chartGroup.append("path")
        .datum(diffSeries)
        .attr("fill", "#6baed6")
        .attr("opacity", 0.6)
        .attr("d", d3.area()
          .x(d => xScale(new Date(d.date)))
          .y0(d => yScale(Math.max(0, d.diff)))
          .y1(() => yScale(0))
          .curve(d3.curveMonotoneX)
        );

      chartGroup.append("path")
        .datum(diffSeries)
        .attr("fill", "#fc8d59")
        .attr("opacity", 0.6)
        .attr("d", d3.area()
          .x(d => xScale(new Date(d.date)))
          .y0(() => yScale(0))
          .y1(d => yScale(Math.min(0, d.diff)))
          .curve(d3.curveMonotoneX)
        );
  
      // Append X-Axis
      chartGroup.append("g")
        .attr("transform", `translate(0, ${reducedHeight})`)
        .call(d3.axisBottom(xScale).ticks(d3.timeMonth.every(1)).tickFormat(d3.timeFormat("%Y-%m")))
        .selectAll("text")
        .attr("dx", "0.5em")
        .attr("dy", "0.5em")
        .attr("transform", "rotate(30)")
        .style("text-anchor", "start")
        .style("font-size", "10px");
  
      // Labels and zero line
      chartGroup.append("line")
        .attr("x1", 0).attr("x2", width)
        .attr("y1", yScale(0)).attr("y2", yScale(0))
        .attr("stroke", "#aaa").attr("stroke-dasharray", "2,2");
      chartGroup.append("text").attr("x", 10).attr("y", yScale(0.35)).text(selectedState1).style("font-size", "12px").style("font-weight", "bold");
      chartGroup.append("text").attr("x", 10).attr("y", yScale(-0.35)).text(selectedState2).style("font-size", "12px").style("font-weight", "bold");
  
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
        ? timeSeriesData.length > 0 ? timeSeriesData : data.filter(d => d.state === currentState)
        : (activeTab === 2 
          ? (emotionTimeSeriesData.length > 0 ? emotionTimeSeriesData.filter(d => d.state === item) : [])
          : (activeTab === 3 
            ? (comparisonData.length > 0 ? comparisonData.filter(d => d.state === item) : [])
            : data.filter(d => d.state === item)));

      // Debug logging
      console.log(`🔍 Chart rendering for ${currentState}:`, {
        isTab1,
        timeSeriesDataLength: timeSeriesData.length,
        chartDataLength: chartData.length,
        currentState,
        item
      });

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

  }, [activeTab, currentState, selectedEmotion, selectedState1, selectedState2, data, margin, width, height, timeSeriesData, loadingTimeSeries, emotionTimeSeriesData, loadingEmotionTimeSeries, comparisonData, loadingComparison]);

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
          onClick={() => {
            setActiveTab(2);
            fetchEmotionTimeSeriesData(selectedEmotion);
          }}
        >
          One emotion across all states
        </button>
        <button
          className={`tab-button ${activeTab === 3 ? "active" : ""}`}
          onClick={() => {
            setActiveTab(3);
            fetchComparisonData(selectedState1, selectedState2, selectedEmotion);
          }}
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
            onChange={(e) => {
              setCurrentState(e.target.value);
              fetchTimeSeriesData(e.target.value);
            }}
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
            onChange={(e) => {
              setSelectedEmotion(e.target.value);
              fetchEmotionTimeSeriesData(e.target.value);
            }}
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
              onChange={(e) => {
                setSelectedState1(e.target.value);
                fetchComparisonData(e.target.value, selectedState2, selectedEmotion);
              }}
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
              onChange={(e) => {
                setSelectedState2(e.target.value);
                fetchComparisonData(selectedState1, e.target.value, selectedEmotion);
              }}
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
            onChange={(e) => {
              setSelectedEmotion(e.target.value);
              fetchComparisonData(selectedState1, selectedState2, e.target.value);
            }}
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
