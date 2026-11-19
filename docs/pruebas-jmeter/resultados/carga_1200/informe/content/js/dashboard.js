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

    var data = {"OkPercent": 42.24340720564566, "KoPercent": 57.75659279435434};
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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.0038999628574965953, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.0, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.0, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.011666666666666667, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.0, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.009583333333333333, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.005, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.0, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.0, 500, 1500, "GET /health"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 8077, 4665, 57.75659279435434, 10533.685402996181, 288, 30131, 4520.0, 30031.0, 30033.0, 30038.0, 87.49106349790941, 79.78776272977643, 18.434984070008017], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 1200, 792, 66.0, 4068.5900000000024, 3356, 6907, 3969.5, 4213.9, 5179.800000000002, 6533.85, 64.86837126331153, 13.047157954484026, 16.4324760797881], "isController": false}, {"data": ["GET /findings", 75, 1, 1.3333333333333333, 3577.746666666667, 3272, 3972, 3596.0, 3700.6000000000004, 3862.6, 3972.0, 9.437523593808985, 210.75010125676354, 3.762106573235183], "isController": false}, {"data": ["POST /auth/login", 1200, 792, 66.0, 25445.684999999987, 288, 30131, 30031.0, 30036.0, 30038.0, 30044.99, 23.571933684293235, 58.98231859432702, 1.909694939891569], "isController": false}, {"data": ["GET /auth/me", 1200, 884, 73.66666666666667, 7746.987499999989, 2472, 30069, 3692.0, 25145.800000000017, 30031.0, 30033.0, 18.503669894529082, 14.537668460494665, 3.752233450780238], "isController": false}, {"data": ["GET /dashboard/summary", 1200, 795, 66.25, 5920.540833333332, 1078, 30035, 5961.0, 6912.9, 14496.100000000004, 27737.28, 28.841993943181272, 9.965979215738114, 6.912995008231985], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 1200, 792, 66.0, 4637.485833333326, 1248, 6952, 4146.5, 6469.0, 6715.9, 6880.98, 73.36757153338225, 14.756626008804107, 18.442200110051356], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 802, 456, 56.85785536159601, 3521.1783042394013, 2954, 4397, 3449.0, 4010.7, 4104.85, 4233.91, 59.69482694454782, 15.631541914774841, 16.241102995906214], "isController": false}, {"data": ["GET /health", 1200, 153, 12.75, 20504.261666666673, 1574, 30046, 20197.0, 30030.0, 30032.0, 30034.0, 18.815560468507456, 10.006331877087352, 3.449182552095583], "isController": false}]}, function(index, item){
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
    createTable($("#errorsTable"), {"supportsControllersDiscrimination": false, "titles": ["Type of error", "Number of errors", "% in errors", "% in all samples"], "items": [{"data": ["401/Unauthorized", 3625, 77.70632368703109, 44.88052494738145], "isController": false}, {"data": ["Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 1040, 22.293676312968916, 12.876067846972886], "isController": false}]}, function(index, item){
        switch(index){
            case 2:
            case 3:
                item = item.toFixed(2) + '%';
                break;
        }
        return item;
    }, [[1, 1]]);

        // Create top5 errors by sampler
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 8077, 4665, "401/Unauthorized", 3625, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 1040, "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": ["GET /dashboard/top-talkers", 1200, 792, "401/Unauthorized", 792, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["GET /findings", 75, 1, "401/Unauthorized", 1, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["POST /auth/login", 1200, 792, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 792, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["GET /auth/me", 1200, 884, "401/Unauthorized", 792, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 92, "", "", "", "", "", ""], "isController": false}, {"data": ["GET /dashboard/summary", 1200, 795, "401/Unauthorized", 792, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 3, "", "", "", "", "", ""], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 1200, 792, "401/Unauthorized", 792, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 802, 456, "401/Unauthorized", 456, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["GET /health", 1200, 153, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 153, "", "", "", "", "", "", "", ""], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
