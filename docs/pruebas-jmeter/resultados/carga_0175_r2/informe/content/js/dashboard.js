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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.9262152777777778, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.9978237214363439, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.9748283752860412, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.92, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [1.0, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.9931506849315068, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.9973460721868365, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.9983296213808464, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.9993946731234867, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.27402135231316727, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [1.0, 500, 1500, "GET /health"], "isController": false}, {"data": [0.9774881516587678, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 8373, 0, 0.0, 166.620446673833, 2, 2262, 137.0, 350.0, 414.0, 529.2600000000002, 94.30222212210971, 475.7730471785638, 35.66606118156528], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 919, 0, 0.0, 169.18280739934707, 7, 581, 155.0, 331.0, 391.0, 471.5999999999999, 11.250122417001274, 1.8567096567121242, 4.3726061737954165], "isController": false}, {"data": ["GET /findings", 874, 0, 0.0, 206.58352402745987, 10, 710, 184.0, 433.0, 503.25, 599.5, 11.024774206569454, 249.4893483289394, 4.424982616113326], "isController": false}, {"data": ["POST /auth/login", 175, 0, 0.0, 279.7085714285714, 55, 2262, 94.0, 497.0000000000002, 1716.2, 2180.680000000001, 8.611357149886821, 18.450505455909852, 2.0519249458714692], "isController": false}, {"data": ["GET /auth/me", 965, 0, 0.0, 137.71606217616582, 5, 496, 114.0, 300.4, 343.69999999999993, 439.0200000000001, 11.261918377350122, 18.586564509493854, 4.124237687017867], "isController": false}, {"data": ["GET /dashboard/summary", 949, 0, 0.0, 186.79662802950503, 12, 616, 172.0, 385.0, 433.5, 518.0, 11.218289713218432, 6.4417522962621465, 4.217814003504977], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 942, 0, 0.0, 173.43842887473468, 7, 557, 171.0, 343.4000000000001, 408.39999999999964, 485.56999999999994, 11.3499445756422, 1.873184212190949, 4.389236378861632], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 898, 0, 0.0, 165.6403118040087, 7, 595, 157.5, 331.1, 365.04999999999995, 462.01, 11.181392568980973, 3.548781821209782, 4.345892814896902], "isController": false}, {"data": ["GET /alerts/unread-count", 826, 0, 0.0, 147.6973365617434, 7, 531, 130.5, 301.0, 357.0, 439.73, 10.76417848206839, 1.8921407488010842, 4.068102609922331], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 843, 0, 0.0, 1498.4270462633453, 145, 2460, 1466.0, 2070.6, 2180.2, 2325.1599999999994, 10.854589701659735, 525.423305760948, 37.18752464574508], "isController": true}, {"data": ["GET /health", 981, 0, 0.0, 72.57798165137616, 2, 311, 55.0, 166.20000000000027, 205.5999999999999, 266.25999999999965, 11.263950764708584, 2.4419893259426813, 4.1139820175791115], "isController": false}, {"data": ["GET /logs", 844, 0, 0.0, 230.6208530805688, 19, 700, 228.5, 433.5, 491.0, 600.6499999999999, 10.836907115893274, 243.98915386417912, 4.148503505302894], "isController": false}]}, function(index, item){
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
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 8373, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
