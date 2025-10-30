import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

function EmotionDifferenceBarChart({ barChartData, dimensions, transform }) {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!barChartData.length) {
      return;
    }
    const margin = dimensions.margin || { top: 20, right: 20, bottom: 20, left: 20 };
    const width = (dimensions.width || 500) - margin.left - margin.right;
    const height = (dimensions.height || 300) - margin.top - margin.bottom;

    const x = d3.scaleLinear().domain([0, 1]).range([0, width]);
    const y = d3.scaleBand().domain(barChartData.map(d => d.emotion)).range([0, height]).padding(0.1);

    const xAxis = g => g
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(x).ticks(5).tickFormat(Math.abs))
      .call(g => g.select(".domain").remove());

    const yAxis = g => g
      .call(d3.axisLeft(y))
      .call(g => g.select(".domain").remove());

    const svg = d3.select(svgRef.current)
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom);

    svg.append('rect')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .attr('fill', 'orange'); // Replace 'white' with the desired background color

    svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`)
      .selectAll("rect")
      .data(barChartData)
      .join("rect")
      .attr("y", d => y(d.emotion))
      .attr("x", d => x(0))
      .attr("width", d => x(Math.abs(d.difference)) - x(0))
      .attr("height", y.bandwidth())
      .attr("fill", d => d.difference > 0 ? "steelblue" : "orange");

    svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`)
      .call(xAxis);

    svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`)
      .call(yAxis);


  }, [barChartData]);

  return <g ref={svgRef} transform={transform}></g>;
}

export default EmotionDifferenceBarChart;
