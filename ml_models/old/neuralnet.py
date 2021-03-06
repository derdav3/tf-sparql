import tensorflow as tf
import re, ast, sys
import numpy as np
from random import sample
# import matplotlib.pyplot as plt

n_nodes_hl1 = 0
n_nodes_hl2 = 0
n_nodes_hl3 = 0
n_nodes_hl4 = 0

x = tf.placeholder('float', [None, 78])
y = tf.placeholder('float', [None, 1])

X_train = np.array([])
Y_train = np.array([])
X_test = np.array([])
Y_test = np.array([])
num_training_samples = 0
batch_size = 80
training_epochs = 400

# Training loop
loss_vec = []
test_loss = []
avg_cost_vec = []

def setting_nodes(l1=100, l2=80, l3=70, l4=60):
	global n_nodes_hl1
	global n_nodes_hl2
	global n_nodes_hl3
	global n_nodes_hl4

	n_nodes_hl1 = l1
	n_nodes_hl2 = l2
	n_nodes_hl3 = l3
	n_nodes_hl4 = l4
# Normalize by column (min-max norm to be between 0 and 1)
def normalize_cols(m):
	col_max = m.max(axis=0)
	col_min = m.min(axis=0)
	return (m-col_min) / (col_max - col_min)

def load_data():
	query_data = []
	global Y_test
	global X_test
	global Y_train
	global X_train
	global num_training_samples

	with open('db-cold-novec-3k.txt-out') as f:
		for line in f:
			line = re.findall(r'\t(.*?)\t', line)
			line = unicode(line[0])
			line = ast.literal_eval(line)
			for _ in line:
				_ = float(_)
			# line[-1] = str(line[-1])
			query_data.append(line)

	y_vals = np.array([ float(x[78])*1000 for x in query_data])

	for l_ in query_data:
		del l_[-1]

	x_vals = np.array(query_data)

	# split into test and train
	l = len(x_vals)
	f = int(round(l*0.8))
	indices = sample(range(l), f)

	X_train = x_vals[indices].astype('float32')
	X_test = np.delete(x_vals, indices, 0).astype('float32')

	Y_train = y_vals[indices].astype('float32')
	Y_test = np.delete(y_vals, indices, 0).astype('float32')

	num_training_samples = X_train.shape[0]
	X_train = np.nan_to_num(normalize_cols(X_train))
	X_test = np.nan_to_num(normalize_cols(X_test))

# Create model
def multilayer_perceptron(x, weights, biases):
    # Hidden layer with RELU activation
    layer_1 = tf.add(tf.matmul(x, weights['h1']), biases['b1'])
    layer_1 = tf.nn.relu(layer_1)

    # Hidden layer with RELU activation
    layer_2 = tf.add(tf.matmul(layer_1, weights['h2']), biases['b2'])
    layer_2 = tf.nn.relu(layer_2)

    # Hidden layer with RELU activation
    layer_3 = tf.add(tf.matmul(layer_2, weights['h3']), biases['b3'])
    layer_3 = tf.nn.relu(layer_3)

    # Output layer with linear activation
    out_layer = tf.add(tf.matmul(layer_3, weights['out']), biases['out'])
    return out_layer

# Store layers weight & bias
weights = {
    'h1': tf.Variable(tf.random_normal([78, n_nodes_hl1], 0, 0.1)),
    'h2': tf.Variable(tf.random_normal([n_nodes_hl1, n_nodes_hl2], 0, 0.1)),
    'h3': tf.Variable(tf.random_normal([n_nodes_hl2, n_nodes_hl3], 0, 0.1)),
    'out': tf.Variable(tf.random_normal([n_nodes_hl3, 1], 0, 0.1))
}
biases = {
    'b1': tf.Variable(tf.random_normal([n_nodes_hl1], 0, 0.1)),
    'b2': tf.Variable(tf.random_normal([n_nodes_hl2], 0, 0.1)),
    'b3': tf.Variable(tf.random_normal([n_nodes_hl3], 0, 0.1)),
    'out': tf.Variable(tf.random_normal([1], 0, 0.1))
}

def train_neural_network(x):
	prediction = multilayer_perceptron(x, weights, biases)
	cost = tf.sqrt(tf.reduce_mean(tf.square(tf.subtract(y, prediction))))
	optimizer = tf.train.AdamOptimizer(0.001).minimize(cost)

	with tf.Session() as sess:
		sess.run(tf.global_variables_initializer())
		for epoch in range(training_epochs):
			temp_loss = 0.
			avg_cost = 0.

			total_batch = int(num_training_samples/batch_size)
			for i in range(total_batch-1):
				batch_x = X_train[i*batch_size:(i+1)*batch_size]
				batch_y = Y_train[i*batch_size:(i+1)*batch_size]
				batch_y = np.transpose([batch_y])
				# Run optimization op (backprop) and cost op (to get loss value)
				_, c, p = sess.run([optimizer, cost, prediction], feed_dict={x: batch_x,
									                                          y: batch_y})
				loss_vec.append(c)
				# Compute average loss
				avg_cost += c / total_batch
				avg_cost_vec.append(avg_cost)

			label_value = batch_y
			estimate = p
			err = label_value-estimate
			# Display logs per epoch step
			if epoch % 3 == 0:
				print ("Epoch:", '%04d' % (epoch+1), "cost=", \
					"{:.9f}".format(avg_cost))
				print ("[*]----------------------------")
				for i in xrange(10):
					print ("label value:", label_value[i], \
						"estimated value:", estimate[i])
				print ("[*]============================")

		perc_err = tf.divide(tf.abs(\
			tf.subtract(y, prediction)), \
			tf.reduce_mean(y))
		correct_prediction = tf.less(tf.cast(perc_err, "float"), 0.2)
		accuracy = tf.reduce_mean(tf.cast(correct_prediction, 'float'))

		mean_relative_error = tf.divide(tf.to_float(tf.reduce_sum(perc_err)), Y_test.shape[0])

		print "Test accuracy: {:.3f}".format(accuracy.eval({x: X_test, y: np.transpose([Y_test])}))
		rel_error = mean_relative_error.eval({x: X_test, y: np.transpose([Y_test])})
		print "relative error: ", rel_error
		return rel_error
		plot_result(loss_vec, avg_cost_vec)

def plot_result(loss_vec, avg_cost_vec):
	# Plot loss (MSE) over time
	plt.plot(loss_vec, 'k-', label='Train Loss')
	plt.plot(avg_cost_vec, 'r--', label='Test Loss')
	plt.title('Loss (MSE) per Generation')
	plt.xlabel('Generation')
	plt.ylabel('Loss')
	plt.show()

def testscript():
	setting_nodes()
	load_data()
	train_neural_network(x)

def main():
	print "hi"
	load_data()
	train_neural_network(x)

if __name__ == '__main__':
	main()
