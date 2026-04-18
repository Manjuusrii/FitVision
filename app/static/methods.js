let scores = []
let endWorkout = false

const wait = (n) => new Promise((resolve) => setTimeout(resolve, n))

// Use a relative URL so the app works on any host/port, not just 127.0.0.1:5000
const BASE_URL = ''

async function toggleRep(start = true, exercise) {
    const postData = {
        method: (start) ? "start-workout" : "end-workout",
        exercise: exercise,
    }

    console.log('Sending fetch request to change method.')
    const response = await fetch(`${BASE_URL}/video`, {
        method: "POST",
        mode: "cors",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(postData),
    })

    console.log('Receiving response.')
    const data = await response.json()
    console.log(data['message'])

    // reloads iframe so the stream reconnects
    console.log('Reloading iframe.')
    $('#webcam').attr('src', function (i, val) { return val })

    if (!start) {
        // Poll until we get a real numeric prediction back
        while (true) {
            let response = await fetch(`${BASE_URL}/get-model-response`, {
                method: "GET",
                mode: "cors",
            })

            let data = await response.json()
            console.log(`Prediction: ${data['response']}`)

            // FIX: original code used `!= NaN` which is always true in JS.
            // Correct check: response must not be the string "null" and must parse as a number.
            if (data['response'] !== 'null' && data['response'] !== 'None' && !isNaN(Number(data['response']))) {
                console.log('Prediction received; ending rep.')
                let prediction = Number(data['response'])
                scores.push(prediction)
                $('#accuracy-score').text(`${prediction}%`)
                return prediction
            } else {
                console.log('Prediction not ready yet, retrying...')
                await wait(500)
            }
        }
    }
}

async function startWorkout() {
    $('#begin-workout').prop('disabled', true)
    $('#end-workout').prop('disabled', false)
    scores = []
    endWorkout = false

    let exercise = $('#exercise-type').find(":selected").val()
    let reps = parseInt($('#exercise-reps').val())
    let repSpeed = parseInt($('#rep-speed').find(":selected").val())
    let sets = parseInt($('#exercise-sets').val())
    let breakLen = parseInt($('#exercise-breaks').val())

    if (!reps || !repSpeed || !sets || !breakLen) {
        alert("Fill in all inputs.")
        $('#begin-workout').prop('disabled', false)
        $('#end-workout').prop('disabled', true)
        return
    }

    // 5-second countdown before starting
    let countdown = $('<h1></h1>')
    for (let i = 5; i > 0; i--) {
        countdown.text(`Starting workout in ${i}...`)
        $('#webcam-container').before(countdown)
        await wait(1000)
    }
    countdown.remove()
    console.log('Workout begun.')

    for (let set = 0; set < sets; set++) {
        console.log(`Beginning set ${set + 1}`)
        for (let rep = 0; rep < reps; rep++) {
            console.log(`Beginning rep ${rep + 1}`)

            // Tell Flask to start recording this rep
            await toggleRep(true, exercise)

            // Count down the rep duration
            countdown = $('<h1></h1>')
            countdown.attr("id", "webcam-header")
            for (let i = repSpeed; i > 0; i--) {
                countdown.text(`Ending rep in ${i}...`)
                $('#webcam-container').before(countdown)
                await wait(1000)
                if (endWorkout) { return }
            }
            countdown.remove()

            // Tell Flask rep has ended and wait for prediction
            await toggleRep(false, exercise)
            await wait(500)
        }

        if (endWorkout) { return }

        // Break between sets (skip break after the last set)
        if (set < sets - 1) {
            countdown = $('<h1></h1>')
            countdown.attr("id", "webcam-header")
            for (let i = breakLen; i > 0; i--) {
                countdown.text(`Starting new set in ${i}...`)
                $('#webcam-container').before(countdown)
                await wait(1000)
            }
            countdown.remove()
        }
    }

    // Show completion message and average score
    let header = $('<h1>Workout complete!</h1>')
    header.attr("id", "completion-header")
    $('#webcam-container').before(header)

    console.log(`All prediction scores: ${scores}`)

    if (scores.length > 0) {
        let avg = scores.reduce((a, b) => a + b, 0) / scores.length
        avg = Math.round(avg * 10) / 10   // round to 1 decimal place
        $('#full-score').text(`Average accuracy score: ${avg}%`)
    } else {
        $('#full-score').text(`Average accuracy score: N/A`)
    }

    $('#begin-workout').prop('disabled', false)
}

async function stopWorkout() {
    $('#end-workout').prop('disabled', true)
    endWorkout = true
    $('#webcam-header').remove()
    $('#completion-header').remove()

    await wait(5000)
    $('#begin-workout').prop('disabled', false)
}