resource "aws_eks_cluster" "cluster" {
  name     = var.cluster_name
  role_arn = var.cluster_role_arn

  vpc_config {
    subnet_ids              = var.subnet_ids
    endpoint_public_access  = true
  }

  kubernetes_network_config {
  }

  compute_config {
    enabled = false
  }

  storage_config {
    block_storage {
      enabled = false
    }
  }
}

resource "aws_eks_node_group" "nodes" {
  cluster_name    = aws_eks_cluster.cluster.name
  node_group_name = "${var.cluster_name}-nodes"
  node_role_arn   = var.node_role_arn
  subnet_ids      = var.subnet_ids

  scaling_config {
    desired_size = var.desired_size
    max_size     = var.max_size
    min_size     = var.min_size
  }

  instance_types = [var.instance_type]

  capacity_type = var.capacity_type

  depends_on = [ aws_eks_cluster.cluster ]
}
