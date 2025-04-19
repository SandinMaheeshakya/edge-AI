import numpy as np
import pandas as pd
import tflite_runtime.interpreter as tflite

# Load the TFLite model
interpreter = tflite.Interpreter(model_path="models\CVD_Classification_Model.tflite")
interpreter.allocate_tensors()

# Get input/output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()


# Convert df to the correct shape and dtype
input_shape = input_details[0]['shape']    # Should be (1, 6)
input_dtype = input_details[0]['dtype']    # Usually np.float32

# Convert df -> numpy array -> reshape -> correct dtype
input_data = df.to_numpy().astype(input_dtype).reshape(input_shape)

# Run inference
interpreter.set_tensor(input_details[0]['index'], input_data)
interpreter.invoke()
output_data = interpreter.get_tensor(output_details[0]['index'])

print("Model output:", output_data)
