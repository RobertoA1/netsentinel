/*
   Licensed to the Apache Software Foundation (ASF) under one or more
   contributor license agreements.  See the NOTICE file distributed with
   this work for additional information regarding copyright ownership.
   The ASF licenses this file to You under the Apache License, Version 2.0
   (the "License"); you may not use this file except in compliance with
   the License.  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/
var showControllersOnly = false;
var seriesFilter = "";
var filtersOnlySampleSeries = true;

/*
 * Add header in statistics table to group metrics by category
 * format
 *
 */
function summaryTableHeader(header) {
    var newRow = header.insertRow(-1);
    newRow.className = "tablesorter-no-sort";
    var cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 1;
    cell.innerHTML = "Requests";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 3;
    cell.innerHTML = "Executions";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 7;
    cell.innerHTML = "Response Times (ms)";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 1;
    cell.innerHTML = "Throughput";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 2;
    cell.innerHTML = "Network (KB/sec)";
    newRow.appendChild(cell);
}

/*
 * Populates the table identified by id parameter with the specified data and
 * format
 *
 */
function createTable(table, info, formatter, defaultSorts, seriesIndex, headerCreator) {
    var tableRef = table[0];

    // Create header and populate it with data.titles array
    var header = tableRef.createTHead();

    // Call callback is available
    if(headerCreator) {
        headerCreator(header);
    }

    var newRow = header.insertRow(-1);
    for (var index = 0; index < info.titles.length; index++) {
        var cell = document.createElement('th');
        cell.innerHTML = info.titles[index];
        newRow.appendChild(cell);
    }

    var tBody;

    // Create overall body if defined
    if(info.overall){
        tBody = document.createElement('tbody');
        tBody.className = "tablesorter-no-sort";
        tableRef.appendChild(tBody);
        var newRow = tBody.insertRow(-1);
        var data = info.overall.data;
        for(var index=0;index < data.length; index++){
            var cell = newRow.insertCell(-1);
            cell.innerHTML = formatter ? formatter(index, data[index]): data[index];
        }
    }

    // Create regular body
    tBody = document.createElement('tbody');
    tableRef.appendChild(tBody);

    var regexp;
    if(seriesFilter) {
        regexp = new RegExp(seriesFilter, 'i');
    }
    // Populate body with data.items array
    for(var index=0; index < info.items.length; index++){
        var item = info.items[index];
        if((!regexp || filtersOnlySampleSeries && !info.supportsControllersDiscrimination || regexp.test(item.data[seriesIndex]))
                &&
                (!showControllersOnly || !info.supportsControllersDiscrimination || item.isController)){
            if(item.data.length > 0) {
                var newRow = tBody.insertRow(-1);
                for(var col=0; col < item.data.length; col++){
                    var cell = newRow.insertCell(-1);
                    cell.innerHTML = formatter ? formatter(col, item.data[col]) : item.data[col];
                }
            }
        }
    }

    // Add support of columns sort
    table.tablesorter({sortList : defaultSorts});
}

$(document).ready(function() {

    // Customize table sorter default options
    $.extend( $.tablesorter.defaults, {
        theme: 'blue',
        cssInfoBlock: "tablesorter-no-sort",
        widthFixed: true,
        widgets: ['zebra']
    });

    var data = {"OkPercent": 66.13198900091659, "KoPercent": 33.86801099908341};
    var dataset = [
        {
            "label" : "FAIL",
            "data" : data.KoPercent,
            "color" : "#FF6347"
        },
        {
            "label" : "PASS",
            "data" : data.OkPercent,
            "color" : "#9ACD32"
        }];
    $.plot($("#flot-requests-summary"), dataset, {
        series : {
            pie : {
                show : true,
                radius : 1,
                label : {
                    show : true,
                    radius : 3 / 4,
                    formatter : function(label, series) {
                        return '<div style="font-size:8pt;text-align:center;padding:2px;color:white;">'
                            + label
                            + '<br/>'
                            + Math.round10(series.percent, -2)
                            + '%</div>';
                    },
                    background : {
                        opacity : 0.5,
                        color : '#000'
                    }
                }
            }
        },
        legend : {
            show : true
        }
    });

    // Creates APDEX table
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.00358997861289337, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.0, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.0, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.017, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.0, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.003, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.0035, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.0, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.0, 500, 1500, "GET /health"], "isController": false}]}, function(index, item){
        switch(index){
            case 0:
                item = item.toFixed(3);
                break;
            case 1:
            case 2:
                item = formatDuration(item);
                break;
        }
        return item;
    }, [[0, 0]], 3);

    // Create statistics table
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 6546, 2217, 33.86801099908341, 10967.067063855782, 88, 30054, 5471.0, 27648.2, 30031.0, 30037.0, 69.93888627719133, 78.26894478663618, 18.732156105095303], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 1000, 382, 38.2, 4964.966999999999, 4425, 7151, 4780.0, 6270.299999999999, 6632.95, 6905.9, 48.7044613286577, 9.055605274693162, 15.11455441505942], "isController": false}, {"data": ["GET /findings", 103, 0, 0.0, 4668.650485436893, 4511, 4932, 4664.0, 4748.0, 4806.2, 4931.84, 10.839823195116818, 245.30392861371288, 4.3507493488213], "isController": false}, {"data": ["POST /auth/login", 1000, 382, 38.2, 23092.388000000014, 88, 30054, 27087.5, 30035.0, 30038.0, 30043.99, 19.76870613818326, 46.47105428980923, 2.911096421864189], "isController": false}, {"data": ["GET /auth/me", 1000, 499, 49.9, 9482.51599999999, 2463, 30048, 4454.5, 30030.0, 30031.0, 30033.99, 15.752496770738162, 19.300254402822848, 3.8597462912715415], "isController": false}, {"data": ["GET /dashboard/summary", 1000, 383, 38.3, 6047.89200000001, 1437, 30037, 5030.5, 9754.699999999999, 15231.349999999993, 28709.950000000004, 24.22480620155039, 10.681105029675388, 7.201083870821221], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 1000, 382, 38.2, 5395.030000000004, 1367, 7160, 5586.0, 6634.9, 6739.95, 7028.58, 58.854687775881345, 10.94283370607969, 18.149544244011537], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 443, 85, 19.187358916478555, 4705.539503386006, 4310, 5284, 4628.0, 5039.2, 5075.8, 5116.04, 27.467757936507937, 8.203112889849951, 9.595114087301587], "isController": false}, {"data": ["GET /health", 1000, 104, 10.4, 20242.202999999965, 2252, 30037, 20502.5, 30017.9, 30031.0, 30033.0, 15.822784810126583, 7.4960443037974684, 3.938451839398734], "isController": false}]}, function(index, item){
        switch(index){
            // Errors pct
            case 3:
                item = item.toFixed(2) + '%';
                break;
            // Mean
            case 4:
            // Mean
            case 7:
            // Median
            case 8:
            // Percentile 1
            case 9:
            // Percentile 2
            case 10:
            // Percentile 3
            case 11:
            // Throughput
            case 12:
            // Kbytes/s
            case 13:
            // Sent Kbytes/s
                item = item.toFixed(2);
                break;
        }
        return item;
    }, [[0, 0]], 0, summaryTableHeader);

    // Create error table
    createTable($("#errorsTable"), {"supportsControllersDiscrimination": false, "titles": ["Type of error", "Number of errors", "% in errors", "% in all samples"], "items": [{"data": ["401/Unauthorized", 1613, 72.75597654488047, 24.641002138710665], "isController": false}, {"data": ["Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 604, 27.24402345511953, 9.227008860372747], "isController": false}]}, function(index, item){
        switch(index){
            case 2:
            case 3:
                item = item.toFixed(2) + '%';
                break;
        }
        return item;
    }, [[1, 1]]);

        // Create top5 errors by sampler
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 6546, 2217, "401/Unauthorized", 1613, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 604, "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": ["GET /dashboard/top-talkers", 1000, 382, "401/Unauthorized", 382, "", "", "", "", "", "", "", ""], "isController": false}, {"data": [], "isController": false}, {"data": ["POST /auth/login", 1000, 382, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 382, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["GET /auth/me", 1000, 499, "401/Unauthorized", 382, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 117, "", "", "", "", "", ""], "isController": false}, {"data": ["GET /dashboard/summary", 1000, 383, "401/Unauthorized", 382, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 1, "", "", "", "", "", ""], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 1000, 382, "401/Unauthorized", 382, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 443, 85, "401/Unauthorized", 85, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["GET /health", 1000, 104, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 104, "", "", "", "", "", "", "", ""], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
