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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.4864145502938893, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.5255972696245734, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.46706586826347307, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.806, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.5555555555555556, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.5192307692307693, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.5303532008830022, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.5122950819672131, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.49936143039591313, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.0, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.6245019920318725, 500, 1500, "GET /health"], "isController": false}, {"data": [0.4641532756489493, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 8219, 0, 0.0, 922.6206351137619, 4, 1696, 932.0, 1359.0, 1435.0, 1543.8000000000002, 92.02055599717859, 455.60959970876206, 34.657816838479796], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 879, 0, 0.0, 931.9135381114894, 35, 1541, 921.0, 1340.0, 1392.0, 1483.2000000000003, 10.708281558365616, 1.7672847493787005, 4.162007871317886], "isController": false}, {"data": ["GET /findings", 835, 0, 0.0, 1093.0299401197615, 281, 1696, 1065.0, 1459.0, 1524.1999999999998, 1629.1999999999998, 10.578323937416862, 239.38623105640715, 4.245792127224932], "isController": false}, {"data": ["POST /auth/login", 250, 0, 0.0, 507.6039999999998, 66, 1503, 325.5, 1279.4, 1359.5, 1491.39, 11.562832431432405, 24.774271830627633, 2.7552061653022526], "isController": false}, {"data": ["GET /auth/me", 963, 0, 0.0, 839.9833852544124, 9, 1532, 863.0, 1284.0, 1362.6, 1443.52, 11.093958803741764, 18.30936560383162, 4.06272905410465], "isController": false}, {"data": ["GET /dashboard/summary", 936, 0, 0.0, 961.3632478632487, 16, 1646, 968.0, 1419.0, 1487.15, 1574.63, 10.957621166003278, 6.292071528915945, 4.119808739171154], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 906, 0, 0.0, 935.6545253863131, 18, 1533, 929.0, 1352.3000000000002, 1413.3, 1496.86, 10.844714697820285, 1.7898015468082304, 4.193854512047688], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 854, 0, 0.0, 995.2107728337236, 24, 1581, 965.5, 1395.0, 1443.75, 1527.45, 10.684749834223728, 3.3911559532448354, 4.152861751973676], "isController": false}, {"data": ["GET /alerts/unread-count", 783, 0, 0.0, 942.2592592592589, 528, 1522, 909.0, 1306.6, 1380.8, 1461.0, 10.370311506675144, 1.82290631953274, 3.9192485869953906], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 798, 0, 0.0, 8409.413533834586, 2220, 10466, 8657.5, 9640.3, 9861.1, 10209.23, 10.429327582826897, 504.8407328219957, 35.73598467212311], "isController": true}, {"data": ["GET /health", 1004, 0, 0.0, 691.7828685258968, 4, 1335, 723.5, 1145.5, 1205.0, 1290.7000000000003, 11.431694486826224, 2.478355640698654, 4.175247791086922], "isController": false}, {"data": ["GET /logs", 809, 0, 0.0, 1094.6773794808387, 548, 1666, 1071.0, 1477.0, 1539.0, 1622.3999999999999, 10.488921158059874, 236.1543723623734, 4.015290130819795], "isController": false}]}, function(index, item){
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
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 8219, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
