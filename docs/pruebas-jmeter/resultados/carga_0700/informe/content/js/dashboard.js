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

    var data = {"OkPercent": 89.33577087141987, "KoPercent": 10.664229128580134};
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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.010112853583467684, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.0, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.0, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.06785714285714285, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.0, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.0, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.0, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.0, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.0, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.0, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.025504151838671413, 500, 1500, "GET /health"], "isController": false}, {"data": [0.0, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 6564, 700, 10.664229128580134, 8506.648842169405, 30, 30032, 5616.0, 30015.0, 30030.0, 30031.0, 60.9714184864895, 213.22415859802427, 19.819609747276072], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 700, 0, 0.0, 5297.159999999998, 3080, 6122, 5330.0, 5789.8, 5944.0, 6046.98, 19.128818932065364, 3.157002343280319, 7.434833920861343], "isController": false}, {"data": ["GET /findings", 700, 190, 27.142857142857142, 12271.177142857143, 5200, 30031, 5716.0, 30030.0, 30030.0, 30031.0, 11.143657666836475, 191.8598005981756, 3.2586803620892764], "isController": false}, {"data": ["POST /auth/login", 700, 0, 0.0, 6760.891428571428, 64, 11786, 7370.0, 10624.599999999999, 11416.949999999992, 11765.82, 21.68726957276079, 46.466669377575364, 5.167669702884407], "isController": false}, {"data": ["GET /auth/me", 750, 48, 6.4, 7524.812000000003, 2993, 30031, 5010.0, 11440.3, 30030.0, 30030.0, 7.158879396745096, 12.290118061852718, 2.453873699470243], "isController": false}, {"data": ["GET /dashboard/summary", 702, 2, 0.2849002849002849, 6094.82905982906, 3117, 30030, 5539.0, 9655.100000000002, 11396.5, 11818.97, 7.016281370873437, 4.071123554516107, 2.630441803344228], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 700, 0, 0.0, 5529.537142857146, 3089, 11776, 5493.5, 6003.4, 7660.999999999993, 11595.93, 17.22907282975215, 2.8434700275665166, 6.662805508380714], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 700, 0, 0.0, 5449.334285714283, 4094, 6143, 5425.5, 5781.0, 5864.95, 6037.98, 19.112627986348123, 6.066019624573379, 7.4285409556314], "isController": false}, {"data": ["GET /alerts/unread-count", 259, 116, 44.78764478764479, 16565.97297297297, 5130, 30031, 6160.0, 30030.0, 30031.0, 30031.0, 5.022299786697692, 6.532610408183052, 1.047972567626527], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 259, 116, 44.78764478764479, 64628.52509652504, 48339, 80803, 54337.0, 79596.0, 79819.0, 80514.0, 2.7359925631707935, 135.52498219029937, 8.931176978576861], "isController": true}, {"data": ["GET /health", 843, 93, 11.03202846975089, 9368.330960854084, 30, 30031, 7542.0, 30018.6, 30030.0, 30031.0, 7.936657377419597, 3.8839266800670336, 2.578950264084507], "isController": false}, {"data": ["GET /logs", 510, 251, 49.21568627450981, 17670.00784313726, 5208, 30032, 7375.0, 30031.0, 30031.0, 30031.0, 8.77902673299709, 111.99036794988208, 1.7067191830341004], "isController": false}]}, function(index, item){
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
    createTable($("#errorsTable"), {"supportsControllersDiscrimination": false, "titles": ["Type of error", "Number of errors", "% in errors", "% in all samples"], "items": [{"data": ["Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 700, 100.0, 10.664229128580134], "isController": false}]}, function(index, item){
        switch(index){
            case 2:
            case 3:
                item = item.toFixed(2) + '%';
                break;
        }
        return item;
    }, [[1, 1]]);

        // Create top5 errors by sampler
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 6564, 700, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 700, "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": ["GET /findings", 700, 190, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 190, "", "", "", "", "", "", "", ""], "isController": false}, {"data": [], "isController": false}, {"data": ["GET /auth/me", 750, 48, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 48, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["GET /dashboard/summary", 702, 2, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 2, "", "", "", "", "", "", "", ""], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": ["GET /alerts/unread-count", 259, 116, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 116, "", "", "", "", "", "", "", ""], "isController": false}, {"data": [], "isController": false}, {"data": ["GET /health", 843, 93, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 93, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["GET /logs", 510, 251, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 251, "", "", "", "", "", "", "", ""], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
