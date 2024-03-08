$(document).ready(function(){
    //add to selection 
    $('.add-to-selection').on("click", function(){
        let button = $(this)
        let id = button.attr("data-index")

        let hotel_id = $("#id").val()
        let hotel_name = $("#hotel_name").val()
        let room_id = $(`.room-id-${id}`).val()
        let room_type = $("#room_type").val()
        let room_name = $("#room_name").val()
        let room_number = $(`.room-number-${id}`).val()
        let room_price = $("#room_price").val()
        let number_of_beds = $("#number_of_beds").val()
        let checkin = $("#checkin").val()
        let checkout = $("#checkout").val()
        let adults = $("#adults").val()
        let children = $("#children").val()


        

        $.ajax({ 
            url:'/booking/add_to_selection/',
            data : {
                "id":id,
                "hotel_id":hotel_id,
                "hotel_name":hotel_name,
                "room_id":room_id,
                "room_type":room_type,
                "room_name":room_name,
                "room_price":room_price,
                "number_of_beds":number_of_beds,
                "room_number":room_number,
                "checkin":checkin,
                "checkout":checkout,
                "adults":adults,
                "children":children,
            }, 
            dataType:"json",
            beforeSend: function(){
                button.html("<i class='fas fa-spinner fa-spin'></i> Processing")
            }, 
            success: function(response){
                button.html("<i class='fas fa-check'></i> Added")
                // console.log(response.total_selected_item);
                $('.room-count').text(response.total_selected_item);
            }
        })

        

       
        
    })
    $('.veiw-selected-type').on("click", function(){
        let button = $(this) 
        // let room_name = button.attr("data-index")
        // let room_image = $("#image").attr("src")

        let roomName = $(this).data('index'); 
        let roomPrice = $("#price").val();
        let roomImage = $(this).find('img').attr('src');

        // // Update elements 
        $('.room-type').text(roomName);
        $('.room-price').text(roomPrice);
        $('.room-image').attr('src', roomImage);

        console.log(roomName);
        // $('.room-type').innerText=room_name
    })
    
})

$(document).on("click",".delete-item",function(){
    let id = $(this).attr("data-item")
    let button = $(this) 
    $.ajax({
        url:'/booking/delete_selection/', 
        data:{ 
            "id":id
        }, 
        dataType:'json',
        beforeSend: function(){
            button.html("<i class='fas fa-spinner fa-spin'></i>")
        }, 
        success: function(res){
            console.log(res.total_selected_item);
            $('.room-count').text(res.total_selected_item);
            $('.selection-list').html(res.data);
        }
    }) 
})

function makeAjaxCall(){
    $.ajax({
        url:"/update_room_status/",
        type:"GET",
        success: function (data) {
            console.log("Checked Rooms");            
        }, 
        
    })
}

setInterval(makeAjaxCall,3000)
//setInterval(makeAjaxCall,86400)