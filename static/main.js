$(document).ready(function(){
    let timerInterval;
    let startTime;

    // Model selection setup
    $("#num-players").on("change", function(){
        var n = parseInt($(this).val());
        var container = $("#players-model");
        container.empty();
        
        // Get the default models from the backend
        $.get("/models", function(models) {
            const defaultModels = [...models, "custom"];
            
            for(var i = 1; i <= n; i++){
                var html = '<div class="form-group mb-3">';
                html += '<label for="player-model-' + i + '">Model for Player ' + i + '</label>';
                html += '<select class="form-control model-select" id="player-model-select-' + i + '">';
                defaultModels.forEach(function(model) {
                    var displayName = model === "custom" ? "Custom Model" : model;
                    html += '<option value="' + model + '">' + displayName + '</option>';
                });
                html += '</select>';
                html += '<input type="text" class="form-control custom-model-input" id="player-model-custom-' + i + '" ' +
                       'placeholder="Enter custom model name" style="display: none;">';
                html += '</div>';
                container.append(html);
            }
            
            // Add change handler for all model selects
            $(".model-select").on("change", function() {
                var customInput = $(this).siblings(".custom-model-input");
                if ($(this).val() === "custom") {
                    customInput.show();
                } else {
                    customInput.hide();
                }
            });
        });
    });
    
    $("#num-players").trigger("change");

    $("#start-btn").click(function(){
        $(this).prop("disabled", true);
        $("#log-messages").empty();
        $("#timer").show();
        startTime = Date.now();
        
        timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            $("#time").text(elapsed);
        }, 1000);

        const apiKey = $("#api-key").val();
        const numPlayers = $("#num-players").val();
        const models = [];
        
        for(let i = 1; i <= numPlayers; i++){
            const selectedValue = $("#player-model-select-" + i).val();
            if (selectedValue === "custom") {
                const customValue = $("#player-model-custom-" + i).val().trim();
                models.push(customValue || "google/gemini-2.0-flash-001");
            } else {
                models.push(selectedValue);
            }
        }

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
                clearInterval(timerInterval);
                $("#timer").hide();
                
                // Format and display the complete game log
                let logOutput = "=== Game Log ===\n\n";
                data.game_log.forEach(event => {
                    if(event.event){ 
                        logOutput += `Event: ${event.event}`;
                        if(event.player) logOutput += ` by ${event.player}`;
                        if(event.cards) logOutput += ` | Cards: ${event.cards.join(", ")}`;
                        if(event.scores) {
                            logOutput += "\nFinal Scores:";
                            for(const [player, score] of Object.entries(event.scores)) {
                                logOutput += `\n  ${player}: ${score}`;
                            }
                        }
                    } else if(event.player && event.action){
                        logOutput += `${event.player}: ${event.action}`;
                        if(event.played_card) logOutput += ` (Played: ${event.played_card})`;
                        if(event.error) logOutput += ` [Error: ${event.error}]`;
                    }
                    logOutput += "\n";
                });
                
                $("#log-messages").text(logOutput);
                $("#start-btn").prop("disabled", false);
            },
            error: function(){
                clearInterval(timerInterval);
                $("#timer").hide();
                $("#log-messages").append("Error running game simulation");
                $("#start-btn").prop("disabled", false);
            }
        });
    });
}); 