import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { pointer } from 'd3-selection';
import SpiderChart from "./SpyderChart";


function EmotionTornadoChart({ colorObjects, data1, data2, dimensions = {}, transform }) {
    const svgRef = useRef(null);
    const spiderChartRef = useRef(null);
    const margin = dimensions.margin || { top: 20, right: 20, bottom: 20, left: 70 };
    const width = (dimensions.width || 800);
    const height = (dimensions.height || 500) - margin.top - margin.bottom;
    const padding = 20;
    var data = [data1, data2];
    data1['color'] = '#1f77b4'
    data2['color'] = '#ff7f0e'
    const showTooltip = (tooltip, event, d, isLeft) => {

        tooltip.transition()
            // .delay(30)
            // .duration(100)
            .style('opacity', 1);
        // tooltip.style('opacity', 1).style('pointer-events', 'none');
        const tooltipText = `Emotion: ${d.emotion}`;
        // tooltip.select(".tooltip-text").text(tooltipText)            
        tooltip.select('.tooltip-text')
            .html('')
            .append('tspan')
            .attr('x', 10)
            .attr('dy', -10)
            .attr('font-size', '1.2em')
            .attr('font-weight', 'bold')
            .text(tooltipText);

        tooltip.select('.tooltip-text')
            .append('tspan')
            .attr('x', 10)
            .attr('dy', '1.2em')
            .text(`Score: ${(isNaN(d.value) ? 0 : d.value).toFixed(3)}`);

        tooltip.select('.tooltip-text')
            .append('tspan')
            .attr('x', 10)
            .attr('dy', '1.2em')
            .text(`State: ${d.state}`);

        // Use pointer() method to get the position relative to the SVG
        const [cursorX, cursorY] = pointer(event);

        const tooltipRect = tooltip.node().getBoundingClientRect();
        const tooltipHeight = tooltipRect.height;
        const tooltipWidth = tooltipRect.width;

        let tooltipX = cursorX + 15;
        let tooltipY = cursorY - tooltipHeight / 2;

        if (isLeft) {
            tooltipX = cursorX - tooltipWidth - 10;
        }

        // Clamp tooltip position to keep it inside the SVG bounds
        const svgRect = svgRef.current.getBoundingClientRect();
        tooltipX = Math.max(0, Math.min(svgRect.width - tooltipWidth, tooltipX));
        tooltipY = Math.max(0, Math.min(svgRect.height - tooltipHeight, tooltipY));

        tooltip.attr("transform", `translate(${tooltipX}, ${tooltipY})`);
    };

    const hideTooltip = (tooltip) => {
        tooltip.style('opacity', 0);
    };

    useEffect(() => {
        if (!data1 || !data2) {
            return;
        }

        console.log("colorObjects", data1);

        const xLeft = d3.scaleLinear().domain([1, 0]).range([0, width / 2]);
        const xRight = d3.scaleLinear().domain([0, 1]).range([0, width / 2 - padding]);
        const y = d3.scaleBand().domain(colorObjects.map(d => d.emotion)).range([margin.top, height]).padding(0.1);

        const xAxisLeft = g => g
            .attr("transform", `translate(${margin.left},${height})`)
            .call(d3.axisTop(xLeft).ticks(5).tickFormat(d3.format(".1f")))
            .selectAll("text")
            .attr("dy", "1.9em");

        const xAxisRight = g => g
            .attr("transform", `translate(${width / 2 + margin.left},${height})`)
            .call(d3.axisTop(xRight).ticks(5).tickFormat(d3.format(".1f")))
            .selectAll("text")
            .attr("dy", "1.9em");

        const gridXLeft = g => g
            .attr("transform", `translate(${margin.left},${margin.top})`)
            .call(d3.axisTop(xLeft).ticks(5).tickSize(-height + margin.top).tickFormat(""))
            .selectAll(".tick")
            .classed("tick-grid", true);

        const gridXRight = g => g
            .attr("transform", `translate(${(width) / 2 + margin.left},${margin.top})`)
            .call(d3.axisTop(xRight).ticks(5).tickSize(-height + margin.top).tickFormat(""))
            .selectAll(".tick")
            .classed("tick-grid", true);

        const yAxis = g => g
            .attr("transform", `translate(${margin.left},0)`)
            .call(d3.axisLeft(y))
            .call(g => g.select(".domain").remove())
        // .selectAll("text")
        // .attr("x", -10) // move the labels to the left of the axis line
        // .attr("dy", ".35em") // center the labels vertically
        // .attr("text-anchor", "end");

        const svg = d3.select(svgRef.current)
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom);

        const chartContainer = svg.append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);

        chartContainer
            .on("click", () => {
                const tooltip = d3.select(svgRef.current.parentNode).select(".tooltip1");
                hideTooltip(tooltip);
            });

        chartContainer.append('rect')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom + 400)
            .attr('fill', 'white');
        const emotions = colorObjects.map(d => d.emotion);

        const transformData = data => {
            return emotions.map(emotion => ({
                state: data.state,
                emotion: emotion,
                value: parseFloat(data[emotion]),
            }));
        };

        const transformedData1 = transformData(data1);
        const transformedData2 = transformData(data2);

        chartContainer.selectAll(".bar1")
            .data(transformedData1)
            .join("rect")
            .attr("class", "bar1")
            .attr("y", d => y(d.emotion))
            .attr("x", d => xLeft(isNaN(d.value) ? 0 : d.value) + margin.left)
            .attr("width", d => width / 2 - xLeft(isNaN(d.value) ? 0 : d.value))
            .attr("height", y.bandwidth())
            .attr("fill", "#1f77b4")
            .style("opacity", 0.5)
            .call((bars) =>
                bars
                    .on("mouseover", (event, d) => {
                        // const tooltip = d3.select(svgRef.current.parentNode).select(".tooltip1");
                        showTooltip(tooltip, event, d, true);
                    })
                    .on('mousemove', (event, d) => showTooltip(tooltip, event, d, true))
                    .on("mouseout", (event, d) => {
                        // const tooltip = d3.select(svgRef.current.parentNode).select(".tooltip1");
                        hideTooltip(tooltip);
                    })
                    .on("click", (event, d) => {
                        // const tooltip = d3.select(svgRef.current.parentNode).select(".tooltip1");
                        hideTooltip(tooltip);
                    })
            );

        chartContainer.selectAll(".bar2")
            .data(transformedData2)
            .join("rect")
            .attr("class", "bar2")
            .attr("y", d => y(d.emotion))
            .attr("x", width / 2 + margin.left)
            .attr("width", d => xRight(isNaN(d.value) ? 0 : d.value))
            .attr("height", y.bandwidth())
            .attr("fill", "#ff7f0e")
            .style("opacity", 0.5)
            .call((bars) =>
                bars
                    .on("mouseover", (event, d) => {
                        // const tooltip = d3.select(svgRef.current.parentNode).select(".tooltip1");
                        showTooltip(tooltip, event, d, false);
                    })
                    .on('mousemove', (event, d) => showTooltip(tooltip, event, d, false))
                    .on("mouseout", (event, d) => {
                        // const tooltip = d3.select(svgRef.current.parentNode).select(".tooltip1");
                        hideTooltip(tooltip);
                    })
                    .on("click", (event, d) => {
                        // const tooltip = d3.select(svgRef.current.parentNode).select(".tooltip1");
                        hideTooltip(tooltip);
                    })
            );



        chartContainer.selectAll(".difference-bar")
            .data(emotions)
            .join("rect")
            .attr("class", "difference-bar")
            .attr("y", d => y(d))
            .attr("x", d => {
                const leftValue = transformData(data1)[emotions.indexOf(d)].value
                const rightValue = transformData(data2)[emotions.indexOf(d)].value
                if (leftValue > rightValue) {
                    return xLeft(leftValue) + margin.left
                } else if (rightValue > leftValue) {
                    return width / 2 + margin.left + xRight(leftValue)
                }
            })
            .attr("width", d => {
                const leftValue = transformData(data1)[emotions.indexOf(d)].value
                const rightValue = transformData(data2)[emotions.indexOf(d)].value
                if (leftValue > rightValue) {
                    return width / 2 - xLeft(leftValue - rightValue)
                } else if (rightValue > leftValue) {
                    return xRight(rightValue - leftValue)
                }
            })
            .attr("height", y.bandwidth())
            .attr("fill", "grey")
            .attr("opacity", 0.8)
            .attr("stroke-dasharray", "4,4");

        chartContainer.selectAll(".value2")
            .data(transformedData2)
            .join("text")
            .attr("class", "value2")
            .attr("y", d => y(d.emotion) + y.bandwidth() / 2)
            .attr("x", d => xRight(isNaN(d.value) ? 0 : d.value) + width / 2 + margin.left + 5)
            .attr("text-anchor", "start")
            .attr("dominant-baseline", "central")
            .text(d => d3.format(".3f")(isNaN(d.value) ? 0 : d.value));


        chartContainer.selectAll(".value1")
            .data(transformedData1)
            .join("text")
            .attr("class", "value1")
            .attr("y", d => y(d.emotion) + y.bandwidth() / 2)
            .attr("x", d => xLeft(isNaN(d.value) ? 0 : d.value) + margin.left - 5)
            .attr("text-anchor", "end")
            .attr("dominant-baseline", "central")
            .text(d => d3.format(".3f")(isNaN(d.value) ? 0 : d.value));

        chartContainer.append("text")
            .attr("class", "state1-info")
            .attr("x", width / 4)
            .attr("y", height + margin.top + 10)
            .attr("text-anchor", "middle")
            .attr("font-size", "20px")
            .text(data1.state + " Score");

        chartContainer.append("text")
            .attr("class", "state2-info")
            .attr("x", (width / 4) * 3)
            .attr("y", height + margin.top + 10)
            .attr("text-anchor", "middle")
            .attr("font-size", "20px")
            .text(data2.state + " Score");

        const tooltip = chartContainer
            // .select('.tooltip1');
            .append("g")
            .attr("class", "tooltip1")
            .style("opacity", 0)
            .style("pointer-events", "none");

        tooltip
            .append("rect")
            .attr("width", 180)
            .attr("height", 50)
            .attr("fill", "#fff2ed")
            .attr("stroke", "black")
            .attr("stroke-width", 1)
            .attr("rx", 5)
            .attr("ry", 5);

        tooltip
            .append("text")
            .attr("class", "tooltip-text")
            .attr("x", 10)
            .attr("y", 25)
            .attr("font-size", "12px")
            .attr("fill", "black");

        chartContainer.append("g")
            .call(xAxisLeft);

        chartContainer.append("g")
            .call(xAxisRight);

        chartContainer.append("g")
            .call(yAxis);

        chartContainer.append("g")
            .call(gridXLeft);

        chartContainer.append("g")
            .call(gridXRight);

        chartContainer.selectAll(".tick-grid")
            .style("stroke-opacity", 0.1)
            .style("shape-rendering", "crispEdges");

        chartContainer.append('rect')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom + 400)
            .attr('fill', 'none')
            .attr('stroke', 'red')
            .attr('stroke-width', 5);

    }, [data1, data2]);

    return (<><g ref={svgRef} transform={transform} ></g>
        <g ref={spiderChartRef} transform={`translate(600, ${height})`}>
            <SpiderChart data={data} />
        </g>
    </>);
}

export default EmotionTornadoChart;
