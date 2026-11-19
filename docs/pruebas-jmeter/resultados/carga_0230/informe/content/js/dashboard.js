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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.522124900466386, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.5492957746478874, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.5123609394313968, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.8434782608695652, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.6107068607068608, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.5646221248630887, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.5620728929384966, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.5473876063183475, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.5266233766233767, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.002564102564102564, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.6732723577235772, 500, 1500, "GET /health"], "isController": false}, {"data": [0.5018987341772152, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 8011, 0, 0.0, 792.4582449132428, 3, 1671, 825.0, 1152.0, 1242.0, 1384.0, 89.40648646235574, 441.8905967500725, 33.68736276115489], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 852, 0, 0.0, 820.1349765258221, 9, 1423, 830.0, 1173.7, 1243.0499999999997, 1331.94, 10.436060754532091, 1.722357683121019, 4.056203301077903], "isController": false}, {"data": ["GET /findings", 809, 0, 0.0, 935.6378244746603, 20, 1510, 923.0, 1229.0, 1313.5, 1419.8, 10.253225520265646, 232.0292919737459, 4.115308289872247], "isController": false}, {"data": ["POST /auth/login", 230, 0, 0.0, 375.12608695652176, 58, 1166, 132.5, 981.7, 1110.35, 1165.07, 10.907711277624966, 23.370623577255053, 2.5991030778715736], "isController": false}, {"data": ["GET /auth/me", 962, 0, 0.0, 713.5135135135134, 7, 1424, 758.0, 1089.4, 1165.5499999999997, 1282.37, 11.109314733122387, 18.334708885719564, 4.068352563399312], "isController": false}, {"data": ["GET /dashboard/summary", 913, 0, 0.0, 830.3296823658267, 13, 1532, 892.0, 1198.2, 1285.1999999999998, 1422.44, 10.719862860900093, 6.1555462521574755, 4.030417188912633], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 878, 0, 0.0, 800.6742596810936, 9, 1503, 823.0, 1177.2, 1256.0, 1382.9400000000005, 10.556564187036347, 1.742245456649553, 4.082421306705462], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 823, 0, 0.0, 826.0996354799511, 9, 1467, 834.0, 1163.0, 1231.3999999999999, 1341.8, 10.210791429386731, 3.240729701709656, 3.9686474500936715], "isController": false}, {"data": ["GET /alerts/unread-count", 770, 0, 0.0, 833.6168831168832, 317, 1368, 837.0, 1114.2999999999997, 1173.35, 1257.1599999999999, 10.200837263526045, 1.7931159252291877, 3.855199239242754], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 780, 0, 0.0, 7136.087179487184, 1048, 9552, 7532.5, 8562.8, 8874.75, 9199.009999999995, 9.982338938800583, 483.2143431333026, 34.22692963890808], "isController": true}, {"data": ["GET /health", 984, 0, 0.0, 573.2489837398368, 3, 1176, 605.0, 941.0, 1013.75, 1084.15, 11.214442013129103, 2.4312559833150984, 4.0958997196389495], "isController": false}, {"data": ["GET /logs", 790, 0, 0.0, 978.5987341772152, 402, 1671, 962.5, 1290.6, 1373.7999999999997, 1482.7200000000003, 10.198943957448456, 229.62563763571694, 3.904283233710737], "isController": false}]}, function(index, item){
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
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 8011, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
