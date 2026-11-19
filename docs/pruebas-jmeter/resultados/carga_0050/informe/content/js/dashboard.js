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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [1.0, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [1.0, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [1.0, 500, 1500, "GET /findings"], "isController": false}, {"data": [1.0, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [1.0, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [1.0, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [1.0, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [1.0, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [1.0, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [1.0, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [1.0, 500, 1500, "GET /health"], "isController": false}, {"data": [1.0, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 2618, 0, 0.0, 14.508021390374351, 2, 129, 11.0, 25.0, 34.0, 71.61999999999989, 29.76962088649337, 152.32014157768756, 11.266403300612906], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 284, 0, 0.0, 11.989436619718308, 5, 70, 10.0, 19.0, 23.0, 47.84999999999957, 3.517899170073083, 0.5805907809983897, 1.367308466493249], "isController": false}, {"data": ["GET /findings", 277, 0, 0.0, 15.671480144404335, 7, 77, 13.0, 24.200000000000017, 32.0, 63.53999999999979, 3.5830703161380453, 81.08446136315128, 1.4381268554030628], "isController": false}, {"data": ["POST /auth/login", 50, 0, 0.0, 62.43999999999998, 51, 115, 58.0, 80.39999999999999, 92.59999999999997, 115.0, 2.5710906566565535, 5.508762598344218, 0.6126426955314445], "isController": false}, {"data": ["GET /auth/me", 301, 0, 0.0, 9.621262458471763, 5, 84, 8.0, 14.0, 19.0, 36.98000000000002, 3.5292600279057766, 5.824657663242932, 1.2924536235006507], "isController": false}, {"data": ["GET /dashboard/summary", 296, 0, 0.0, 17.570945945945947, 8, 126, 14.0, 26.0, 32.299999999999955, 88.08999999999992, 3.544231045548158, 2.0351639206858563, 1.3325478052109774], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 289, 0, 0.0, 13.59515570934256, 7, 105, 11.0, 22.0, 25.5, 40.600000000000136, 3.512738234150136, 0.5797390249720439, 1.358441738987748], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 279, 0, 0.0, 12.197132616487451, 6, 102, 9.0, 19.0, 25.0, 65.79999999999995, 3.550205504727245, 1.126774208043315, 1.3798650301576596], "isController": false}, {"data": ["GET /alerts/unread-count", 263, 0, 0.0, 11.832699619771864, 5, 117, 9.0, 18.0, 24.799999999999983, 60.16000000000008, 3.5507911648755197, 0.624162509450775, 1.3419493953191661], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 269, 0, 0.0, 124.15985130111522, 81, 284, 114.0, 176.0, 204.0, 237.90000000000026, 3.5396599821043213, 171.33815790880442, 12.123916266974579], "isController": true}, {"data": ["GET /health", 310, 0, 0.0, 4.890322580645163, 2, 96, 4.0, 7.0, 10.0, 24.679999999999836, 3.5842293906810037, 0.7770497311827957, 1.3090837813620073], "isController": false}, {"data": ["GET /logs", 269, 0, 0.0, 26.23420074349441, 16, 129, 22.0, 39.0, 48.0, 115.90000000000003, 3.547408677304497, 79.86865923364763, 1.3579923842806279], "isController": false}]}, function(index, item){
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
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 2618, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
