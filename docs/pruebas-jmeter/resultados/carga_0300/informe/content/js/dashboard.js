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

    var data = {"OkPercent": 100.0, "KoPercent": 0.0};
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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.3116511392973398, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.3511111111111111, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.18427672955974841, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.47333333333333333, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.4149590163934426, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.2927215189873418, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.341792656587473, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.3451118963486455, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.389196675900277, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.0, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.48009950248756217, 500, 1500, "GET /health"], "isController": false}, {"data": [0.15492021276595744, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 8173, 0, 0.0, 1436.9889881316512, 4, 3002, 1443.0, 1752.0, 2327.5999999999985, 2763.0, 91.08943995541934, 430.5968323349123, 34.2168670764837], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 900, 0, 0.0, 1463.974444444446, 37, 2840, 1432.5, 1646.2999999999997, 2037.5499999999993, 2691.0, 10.880471970695263, 1.7957028936010735, 4.228933441735073], "isController": false}, {"data": ["GET /findings", 795, 0, 0.0, 1608.0817610062902, 1065, 2966, 1548.0, 1781.8, 2373.799999999997, 2890.3199999999997, 10.087936350831779, 228.28881743928204, 4.048966640812364], "isController": false}, {"data": ["POST /auth/login", 300, 0, 0.0, 1198.4333333333332, 70, 2824, 1116.5, 2668.8, 2745.85, 2805.95, 13.273748949161542, 28.440044135215256, 3.1628854917923985], "isController": false}, {"data": ["GET /auth/me", 976, 0, 0.0, 1364.4159836065576, 10, 2795, 1385.0, 1880.1000000000004, 2436.2, 2721.46, 11.214523727450304, 18.508344823624036, 4.10688124784557], "isController": false}, {"data": ["GET /dashboard/summary", 948, 0, 0.0, 1465.3164556962022, 19, 2884, 1489.0, 1740.4, 2259.149999999996, 2808.5299999999997, 11.112022786679638, 6.3807318345386985, 4.177860129757481], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 926, 0, 0.0, 1451.6619870410373, 17, 2842, 1450.0, 1661.6000000000001, 2083.5999999999995, 2726.92, 11.028798742288178, 1.82018260492842, 4.265043263619257], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 849, 0, 0.0, 1492.767962308598, 617, 2874, 1437.0, 1649.0, 2135.0, 2756.5, 10.49041776327983, 3.329478294009712, 4.077330341587278], "isController": false}, {"data": ["GET /alerts/unread-count", 722, 0, 0.0, 1421.480609418282, 920, 2824, 1401.5, 1566.0, 1603.7, 2620.6399999999994, 10.035025296047145, 1.7639692903207873, 3.792533974189693], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 736, 0, 0.0, 13153.077445652165, 7402, 16148, 12849.0, 15406.800000000001, 15636.05, 15953.27, 9.562042847306127, 462.8586781060399, 32.76343017987294], "isController": true}, {"data": ["GET /health", 1005, 0, 0.0, 1212.9243781094524, 4, 2571, 1240.0, 1806.1999999999998, 2298.3999999999996, 2526.8199999999997, 11.381524558045776, 2.4674789569200803, 4.156924008504999], "isController": false}, {"data": ["GET /logs", 752, 0, 0.0, 1610.7606382978738, 1100, 3002, 1557.5, 1733.7, 2214.5, 2924.7000000000003, 9.993355481727574, 224.9968853820598, 3.8255813953488373], "isController": false}]}, function(index, item){
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
    createTable($("#errorsTable"), {"supportsControllersDiscrimination": false, "titles": ["Type of error", "Number of errors", "% in errors", "% in all samples"], "items": []}, function(index, item){
        switch(index){
            case 2:
            case 3:
                item = item.toFixed(2) + '%';
                break;
        }
        return item;
    }, [[1, 1]]);

        // Create top5 errors by sampler
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 8173, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
