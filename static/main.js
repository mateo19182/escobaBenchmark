$(document).ready(function(){
    // Dynamically update the model input fields based on number of players.
    $("#num-players").on("change", function(){
         var n = parseInt($(this).val());
         var container = $("#players-model");
         container.empty();
         for(var i = 1; i <= n; i++){
              var html = '<div class="form-group">';
              html += '<label for="player-model-' + i + '">Model for AI Player ' + i + ' (default: openai/gpt-4o):</label>';
              html += '<input type="text" class="form-control" id="player-model-' + i + '" placeholder="openai/gpt-4o">';
              html += '</div>';
              container.append(html);
         }
    });
    // Trigger change event on load to fill in the default fields.
    $("#num-players").trigger("change");

    $("#start-btn").click(function(){
         $(this).prop("disabled", true);
         $("#log-messages").empty();
         $("#final-scores").empty();
         $("#table-cards").empty();
         $("#player-list").empty();

         // Gather setup form inputs.
         var apiKey = $("#api-key").val();
         var numPlayers = $("#num-players").val();
         var models = [];
         for(var i = 1; i <= numPlayers; i++){
              var model = $("#player-model-" + i).val();
              models.push(model);
         }

         // Send AJAX POST request with the configuration.
         $.ajax({
              url: "/simulate",
              type: "POST",
              contentType: "application/json",
              data: JSON.stringify({
                  "api_key": apiKey,
                  "num_players": numPlayers,
                  "models": models
              }),
              success: function(data){
                   var game_log = data.game_log;
                   var final_scores = data.final_scores;
                   
                   // Display players based on final scores.
                   var n = Object.keys(final_scores).length;
                   for(var i = 1; i <= n; i++){
                         var playerDiv = $('<div class="col-md-4" id="player-' + i + '"><h4>AI Player ' + i + '</h4><div class="hand"></div><div class="captured"></div></div>');
                         $("#player-list").append(playerDiv);
                   }

                   var currentLogIndex = 0;
                   function processNextEvent(){
                        if(currentLogIndex < game_log.length){
                              var event = game_log[currentLogIndex];
                              var message = "";
                              if(event.event){ 
                                 // Special events like "immediate_capture", "finalize_round", etc.
                                 message = "<strong>Event:</strong> " + event.event;
                                 if(event.player){
                                    message += " by " + event.player;
                                 }
                                 if(event.cards){
                                    message += " | Cards: " + event.cards.join(", ");
                                 }
                              } else if(event.player && event.action){
                                   message = "<strong>" + event.player + ":</strong> " + event.action;
                                   if(event.played_card){
                                       message += " (Played: " + event.played_card + ")";
                                   }
                                   if(event.error){
                                       message += " <span style='color:red;'>[Error: " + event.error + "]</span>";
                                   }
                                   // Update table display if available.
                                   if(event.table_after){
                                       var tableHtml = "";
                                       event.table_after.forEach(function(card){
                                          tableHtml += '<span class="card-display">' + card + '</span>';
                                       });
                                       $("#table-cards").html(tableHtml);
                                   }
                              } else {
                                  message = JSON.stringify(event);
                              }
                              $("#log-messages").append("<div>" + message + "</div>");
                              currentLogIndex++;
                              setTimeout(processNextEvent, 1500);
                        } else {
                             // After processing, show final scores.
                             var finalHtml = "<h3>Final Scores</h3><ul>";
                             $.each(final_scores, function(player, score){
                                  finalHtml += "<li>" + player + ": " + score + "</li>";
                             });
                             finalHtml += "</ul>";
                             $("#final-scores").html(finalHtml);
                             $("#start-btn").prop("disabled", false);
                        }
                   }
                   processNextEvent();
              },
              error: function(xhr, status, error){
                      console.error("Simulation error", error);
                      $("#log-messages").append("<div style='color:red;'>Simulation failed: " + error + "</div>");
                      $("#start-btn").prop("disabled", false);
              }
         });
    });
}); 