$(document).ready(function(){
    //add to selection 
    $('.add-to-selection').on("click", function(){
        let button = $(this)
        let id = button.attr("data-index")

        // let id = $("#hotel-id").val()
        let hotel_id = $("#hotel-id").val()
        let hotel_name = $("#hotelname").val()
        let room_id = $(`.room-id-${id}`).val()
        let room_type = $("#room-type").val()
        let room_number = $(`.room-number-${id}`).val()
        let room_price = $("#room-price").val()
        let number_of_beds = $("#room-beds").val()
        let checkin = $("#checkin").val()
        let checkout = $("#checkout").val()
        let adults = $("#adults").val()
        let children = $("#children").val()

        $.ajax({
            url:'booking/add_to_selection', 
            data: {
                "id":id,
                "hotel_id":hotel_id,
                "hotel_name":hotel_name,
                "room_id":room_id,
                "room_type":room_type,
                "room_number":room_number,
                "room_price":room_price,
                "number_of_beds":number_of_beds,
                "checkin":checkin,
                "checkout":checkout,
                "adults":adults,
                "children":children,
            },
            dataType:"json",
            beforeSend:function(){
                console.log("sending data to server");
            },
            success: function(response){
                console.log(response);
            },
        })
        
    })
})