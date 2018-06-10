<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
</head>
<body>
<h1>Thread Mill G-Code Generator</h1>
<p>
    Create a program to generate a callable g-code sub program 
    to mill an internal thread with a 1 pass thread mill such 
    as <a href="Catalog2015_81015_30DEGREE_UN_HELICAL.pdf">these</a>.
</p>
<p>
    <h2>Program Inputs</h2>
    <h3>Thread Information</h3>
    <ul>
        <li>Major Diameter</li>
        <li>Minor Diameter</li>
        <li>Thread Depth</li>
        <li>Absolute "Z" of starting plane</li>
        <li>Threads per inch</li>
    </ul>
    <h3>Number of radial passes</h3>
    <ul>
        <li>1 - 100%</li>
        <li>2 - 65%, 35%</li>
        <li>3 - 50%, 30%, 20%</li>
        <li>4 - 40%, 27%, 20%, 13%</li>
    </ul>
    <h3>Tool Parameters</h3>
    <ul>
        <li>Tool diameter</li>
        <li>Number of flutes</li>
        <li>Speed (SFM)</li>
        <li>Feed per tooth</li>
    </ul>
</p>
</body>
</html>
