function displaySubject() {
    var value = $('#billRelationSelect').children('option:selected').text()
    console.log(value);
    if (value == 'Sponsor')
        displaySponsored();
    else if (value == 'Sponsor (116th)')
        displaySponsoredNow();
    else if (value == 'Cosponsor')
        displayCosponsored();
}

function displaySponsored() {
    $.getJSON('./data/count/sponsor_subj/', function(data) {
        displayCount(data['res'], '#sponsoredDiv');
    });
}

function displaySponsoredNow() {
    $.getJSON('./data/count/sponsor_subj_now/', function(data) {
        displayCount(data['res'], '#sponsoredNowDiv');
    });
}

function displayCosponsored() {
    $.getJSON('./data/count/cosponsor_subj/', function(data) {
        displayCount(data['res']);
    });
}

function displayCount(data, div) {
    $(div).empty();
    var h = 600;
    var w = 800;
    var margin_fact = 0.25;

    // set the dimensions and margins of the graph
    var margin = {top: h * margin_fact, right: w * margin_fact, bottom: h * margin_fact, left: w * margin_fact},
    width = w - margin.left - margin.right,
    height = h - margin.top - margin.bottom;

    // append the svg object to the body of the page
    var svg = d3.select(div)
                .append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
                .append("g")
                .attr("transform",
                      "translate(" + margin.left + "," + margin.top + ")");

    var vals = data.map(function(d) { return d.value; })
    var mx = Math.max(...vals)

    // Add X axis
    var x = d3.scaleLinear()
        .domain([0, mx])
        .range([ 0, width]);

    svg.append("g")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(x))
        .selectAll("text")
        .attr("transform", "translate(-10,0)rotate(-45)")
        .style("text-anchor", "end");

    // Y axis
    var y = d3.scaleBand()
        .range([ 0, height ])
        .domain(data.map(function(d) { return d.label; }))
        .padding(.1);

    svg.append("g")
        .call(d3.axisLeft(y))

    // Add a tooltip div. Here I define the general feature of the tooltip: stuff that do not depend on the data point.
    // Its opacity is set to 0: we don't see it by default.
    var tooltip = d3.select(div)
        .append("div")
            .style("opacity", 0)
            .attr("class", "tooltip")
            .style("background-color", "white")
            .style("border", "solid")
            .style("border-width", "1px")
            .style("border-radius", "5px")
            .style("padding", "10px")

    // A function that change this tooltip when the user hover a point.
    // Its opacity is set to 1: we can now see it. Plus it set the text and position of tooltip depending on the datapoint (d)
    var mouseover = function(d) {
        tooltip
            .style("opacity", 1)
    }

    var mousemove = function(d) {
        tooltip
        .html("# of Bills: " + d.value)
        .style("left", (d3.mouse(this)[0]+90) + "px") // It is important to put the +90: other wise the tooltip is exactly where the point is an it creates a weird effect
        .style("top", (d3.mouse(this)[1]) + "px")
    }

    // A function that change this tooltip when the leaves a point: just need to set opacity to 0 again
    var mouseleave = function(d) {
        tooltip
            .transition()
            .duration(200)
            .style("opacity", 0)
    }

    //Bars
    svg.selectAll("myRect")
        .data(data)
        .enter()
        .append("rect")
        .attr("x", x(0) )
        .attr("y", function(d) { return y(d.label); })
        .attr("width", function(d) { return x(0); })
        .attr("height", y.bandwidth() )
        .attr("fill", "#69b3a2")
        .on("mouseover", mouseover )
        .on("mousemove", mousemove )
        .on("mouseleave", mouseleave )

    // Animation
    svg.selectAll("rect")
        .transition()
        .duration(800)
        .attr("x", function(d) { return x(0); })
        .attr("width", function(d) { return x(d.value); })
        .delay(function(d,i){console.log(i) ; return(i*100)})

}
