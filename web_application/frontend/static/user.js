

$(document).ready(function(){
                $('[data-toggle="tooltip"]').tooltip();
                $(".progress-bar").loading();
                document.getElementById("created-at").innerHTML=document.getElementById("created-at").innerHTML.replace(" +0000", "");
                var results = parseTweets(JSON.parse(document.getElementById("tweets").innerHTML)); //Multiple tweets in an array

                //output

                document.getElementById("tweets").innerHTML="";
                for (var i = 0; i < results.length; i++) {
                    let div = document.createElement('div');
                    div.className = "tweet";
                    div.innerHTML += '<div class="tweet-header">'
                       +'<img src="'+document.getElementById("profile-image").innerHTML+'" alt="" class="avator">'
                       + '<div class="tweet-header-info">'
                       + document.getElementById("name").innerHTML+'<span>'+document.getElementById("screen-name").innerHTML+'</span>  <span id="tweet-time">  &#8226  <a href="https://twitter.com/'+document.getElementById("screen-name-raw").innerHTML+'/status/'+results[i].id_str+'" target="_blank">'+results[i].created_at.replace(" +0000", "")+'</a></span></div></div>'
                    div.innerHTML +='<div class="tweet-content">' +results[i].html+ '</div>';
                    div.innerHTML += '<div class="tweet-info-counts"><div class="retweets"><svg class="feather feather-repeat sc-dnqmqq jxshSx" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="17 1 21 5 17 9"></polyline><path d="M3 11V9a4 4 0 0 1 4-4h14"></path><polyline points="7 23 3 19 7 15"></polyline><path d="M21 13v2a4 4 0 0 1-4 4H3"></path></svg><div class="retweet-count">'+results[i].retweet_count+'</div></div><div class="likes"><svg class="feather feather-heart sc-dnqmqq jxshSx" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg><div class="likes-count">'+results[i].favorite_count+'</div></div></div>'
                   document.getElementById('tweets').appendChild(div);
                }

                $(".text.found-tweet").each(function(i, obj){
                        console.log("*****************");
                        console.log(obj.innerHTML);
                        var result = parseFoundTweet(JSON.parse(obj.innerHTML));
                        obj.innerHTML=result.html;
                });


            });